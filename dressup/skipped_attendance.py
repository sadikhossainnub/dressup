# Copyright (c) 2026, Prime Technology of Bangladesh and contributors
# For license information, please see license.txt

"""Recheck and fix Employee Checkins whose *skip_auto_attendance* flag was set
because an auto-Absent attendance already existed when late biometric punches arrived.

Key design feature:
    Does NOT cancel the Attendance record! Updates it directly in-place:
    - Status changes from Absent -> Present / Half Day
    - Working hours, in_time, out_time, shift, overtime properly calculated & saved
    - Employee Checkin records are linked to the Attendance and un-skipped
    - Full audit comment logged on the Attendance doc
    - Works even if Salary Slip is linked (no cancel errors)
"""

from __future__ import annotations

from datetime import datetime
from itertools import groupby

import frappe
from frappe import _
from frappe.utils import cint, flt, getdate

from hrms.hr.doctype.employee_checkin.employee_checkin import (
	get_overtime_data,
	mark_attendance_and_link_log,
)
from hrms.hr.doctype.shift_assignment.shift_assignment import get_employee_shift


# ---------------------------------------------------------------------------
# Public APIs
# ---------------------------------------------------------------------------

@frappe.whitelist()
def recheck_skipped_attendance(
	shift_type: str | None = None,
	from_date: str = "",
	to_date: str = "",
	employee: str | None = None,
	dry_run: int | bool = 1,
) -> dict:
	"""Bulk scan and update skipped checkins in-place without cancelling Attendance.

	Can be triggered from Shift Type or Attendance List View.
	"""
	dry_run = int(dry_run)

	if shift_type:
		shift_doc = frappe.get_doc("Shift Type", shift_type)
		shift_doc.check_permission("write")
	else:
		frappe.has_permission("Attendance", "write", throw=True)

	# 1. Fetch skipped checkins
	logs = _get_skipped_checkins(shift_type, from_date, to_date, employee)
	if not logs:
		return {
			"dry_run": dry_run,
			"to_fix": [],
			"untouched": [],
			"failed": [],
			"process_message": _("No skipped checkins found for the given filters."),
		}

	# 2. Group by (employee, attendance_date)
	group_key = lambda log: (log.employee, getdate(log.shift_start or log.time))
	sorted_logs = sorted(logs, key=group_key)

	to_fix: list[dict] = []
	untouched: list[dict] = []
	failed: list[dict] = []

	for (emp, att_date), group_iter in groupby(sorted_logs, key=group_key):
		group_logs = list(group_iter)
		emp_name = group_logs[0].employee_name
		checkin_names = [l.name for l in group_logs]

		# Resolve shift for this group
		resolved_shift = _resolve_shift(shift_type, group_logs, emp, att_date)
		if not resolved_shift:
			failed.append(
				_row(
					emp,
					emp_name,
					att_date,
					checkin_names,
					None,
					_("Cannot determine Shift Type"),
				)
			)
			continue

		# Calculate what the attendance would be from these checkins
		(
			calc_status,
			working_hours,
			late_entry,
			early_exit,
			in_time,
			out_time,
		) = _calculate_attendance(resolved_shift, emp, att_date, group_logs)

		# Find existing attendance for this employee + date
		attendance = _get_submitted_attendance(emp, att_date)

		if not attendance:
			# No attendance existed at all
			target_remark = _("No Attendance → will mark {0} ({1}h)").format(
				calc_status, working_hours
			)
			to_fix.append(
				_row(emp, emp_name, att_date, checkin_names, None, target_remark)
			)
			if not dry_run:
				try:
					overtime_type = group_logs[0].get("overtime_type")
					mark_attendance_and_link_log(
						group_logs,
						calc_status,
						att_date,
						working_hours,
						late_entry,
						early_exit,
						in_time,
						out_time,
						resolved_shift.name,
						overtime_type,
					)
				except Exception as exc:
					failed.append(
						_row(emp, emp_name, att_date, checkin_names, None, str(exc))
					)
			continue

		# If an Attendance exists: check if it's an auto-marked Absent
		if not _is_auto_marked_absent(attendance):
			# Present / Half Day / On Leave / manual Absent — keep untouched
			untouched.append(
				_row(
					emp,
					emp_name,
					att_date,
					checkin_names,
					attendance.name,
					_("Kept as-is ({0})").format(attendance.status),
				)
			)
			continue

		# Auto-marked Absent found — update it in-place!
		target_remark = _("Auto-Absent → will update to {0} ({1}h)").format(
			calc_status, working_hours
		)
		to_fix.append(
			_row(emp, emp_name, att_date, checkin_names, attendance.name, target_remark)
		)

		if not dry_run:
			try:
				_update_attendance_in_place(
					attendance.name,
					resolved_shift,
					calc_status,
					working_hours,
					late_entry,
					early_exit,
					in_time,
					out_time,
					checkin_names,
					group_logs,
				)
			except Exception as exc:
				failed.append(
					_row(
						emp,
						emp_name,
						att_date,
						checkin_names,
						attendance.name,
						str(exc),
					)
				)

	if not dry_run and not frappe.flags.in_test:
		frappe.db.commit()  # nosemgrep

	process_message = ""
	if dry_run:
		if to_fix:
			process_message = _(
				"{0} record(s) can be updated to Present/Half Day. Click 'Fix Now' to apply."
			).format(len(to_fix))
		else:
			process_message = _("Nothing to fix.")
	else:
		process_message = _(
			"Successfully updated {0} attendance record(s) in-place."
		).format(len(to_fix) - len(failed))

	return {
		"dry_run": dry_run,
		"to_fix": to_fix,
		"untouched": untouched,
		"failed": failed,
		"process_message": process_message,
	}


@frappe.whitelist()
def recheck_single_attendance(attendance_name: str, dry_run: int | bool = 1) -> dict:
	"""Recheck skipped checkins for a specific Attendance document and update it in-place."""
	dry_run = int(dry_run)

	att = frappe.get_doc("Attendance", attendance_name)
	att.check_permission("write")

	if att.docstatus != 1:
		frappe.throw(_("Attendance must be submitted to recheck."))

	att_date = att.attendance_date
	emp = att.employee

	# Fetch checkins for this employee on this date
	# Include both unlinked and already linked to this attendance
	logs = frappe.get_all(
		"Employee Checkin",
		filters={
			"employee": emp,
			"time": (
				"between",
				[
					datetime.combine(getdate(att_date), datetime.min.time()),
					datetime.combine(getdate(att_date), datetime.max.time()),
				],
			),
		},
		fields=[
			"name",
			"employee",
			"employee_name",
			"shift_start",
			"shift_end",
			"shift_actual_start",
			"shift_actual_end",
			"log_type",
			"time",
			"shift",
			"device_id",
			"overtime_type",
			"skip_auto_attendance",
			"attendance",
		],
		order_by="time",
	)

	# Filter: Keep only unlinked OR linked to this specific attendance
	logs = [
		log for log in logs 
		if not log.get("attendance") or log.get("attendance") == att.name
	]

	if not logs:
		return {
			"found": False,
			"message": _("No check-in logs found for this employee on {0}.").format(
				att_date
			),
		}

	resolved_shift = _resolve_shift(att.shift, logs, emp, att_date)
	if not resolved_shift:
		frappe.throw(_("Could not determine Shift Type for employee {0}.").format(emp))

	(
		calc_status,
		working_hours,
		late_entry,
		early_exit,
		in_time,
		out_time,
	) = _calculate_attendance(resolved_shift, emp, att_date, logs)

	checkin_names = [l.name for l in logs]

	if dry_run:
		return {
			"found": True,
			"dry_run": 1,
			"attendance": att.name,
			"current_status": att.status,
			"new_status": calc_status,
			"working_hours": working_hours,
			"in_time": str(in_time) if in_time else "",
			"out_time": str(out_time) if out_time else "",
			"late_entry": bool(late_entry),
			"early_exit": bool(early_exit),
			"checkin_count": len(logs),
			"shift": resolved_shift.name,
		}

	# Apply in-place update
	_update_attendance_in_place(
		att.name,
		resolved_shift,
		calc_status,
		working_hours,
		late_entry,
		early_exit,
		in_time,
		out_time,
		checkin_names,
		logs,
	)

	if not frappe.flags.in_test:
		frappe.db.commit()  # nosemgrep

	return {
		"found": True,
		"dry_run": 0,
		"success": True,
		"new_status": calc_status,
		"working_hours": working_hours,
		"message": _(
			"Attendance {0} updated to {1} ({2} hrs) and {3} checkin log(s) linked."
		).format(att.name, calc_status, working_hours, len(logs)),
	}


# ---------------------------------------------------------------------------
# Internal Helpers
# ---------------------------------------------------------------------------

def _calculate_attendance(shift_doc, employee: str, attendance_date, logs: list):
	"""Calculate attendance status and timings using Shift Type rules."""
	working_hours_threshold_for_half_day = flt(shift_doc.working_hours_threshold_for_half_day)
	working_hours_threshold_for_absent = flt(shift_doc.working_hours_threshold_for_absent)

	if shift_doc.is_half_holiday(employee, attendance_date):
		working_hours_threshold_for_half_day = working_hours_threshold_for_half_day / 2
		working_hours_threshold_for_absent = working_hours_threshold_for_absent / 2

	return shift_doc.get_attendance(
		logs,
		working_hours_threshold_for_absent,
		working_hours_threshold_for_half_day,
	)


def _update_attendance_in_place(
	attendance_name: str,
	shift_doc,
	status: str,
	working_hours: float,
	late_entry: int | bool,
	early_exit: int | bool,
	in_time,
	out_time,
	checkin_names: list[str],
	logs: list[dict],
):
	"""Update Attendance record in-place without cancelling, and link checkins."""
	update_values = {
		"status": status,
		"working_hours": working_hours,
		"late_entry": cint(late_entry),
		"early_exit": cint(early_exit),
		"in_time": in_time,
		"out_time": out_time,
		"shift": shift_doc.name,
	}

	# Check overtime if Present
	overtime_type = logs[0].get("overtime_type")
	if overtime_type and status == "Present":
		overtime_data = get_overtime_data(shift_doc.name, working_hours)
		if overtime_data:
			update_values.update({
				"overtime_type": overtime_type,
				"standard_working_hours": overtime_data.get("standard_working_hours"),
				"actual_overtime_duration": overtime_data.get("actual_overtime_duration"),
			})

	# 1. Update Attendance row directly in DB
	frappe.db.set_value("Attendance", attendance_name, update_values)

	# 2. Link checkins and reset skip flag
	EmployeeCheckin = frappe.qb.DocType("Employee Checkin")
	(
		frappe.qb.update(EmployeeCheckin)
		.set("attendance", attendance_name)
		.set("skip_auto_attendance", 0)
		.where(EmployeeCheckin.name.isin(checkin_names))
	).run()

	# 3. Add audit comment
	comment_text = _(
		"Attendance updated in-place from {0} skipped Employee Checkin(s). "
		"Status: {1}, Working Hours: {2}."
	).format(
		len(checkin_names),
		frappe.bold(status),
		frappe.bold(str(working_hours)),
	)
	frappe.get_doc({
		"doctype": "Comment",
		"comment_type": "Comment",
		"reference_doctype": "Attendance",
		"reference_name": attendance_name,
		"content": comment_text,
	}).insert(ignore_permissions=True)


def _resolve_shift(shift_type: str | None, logs: list[dict], employee: str, attendance_date):
	"""Determine Shift Type from parameter, checkin logs, or employee's shift assignment."""
	shift_name = shift_type or (logs[0].get("shift") if logs else None)

	if not shift_name:
		timestamp = datetime.combine(getdate(attendance_date), datetime.min.time())
		shift_details = get_employee_shift(employee, timestamp, True)
		if shift_details and shift_details.shift_type:
			shift_name = shift_details.shift_type.name

	if not shift_name:
		shift_name = frappe.db.get_value("Employee", employee, "default_shift")

	if shift_name:
		return frappe.get_doc("Shift Type", shift_name)
	return None


def _get_skipped_checkins(
	shift_type: str | None,
	from_date: str,
	to_date: str,
	employee: str | None = None,
) -> list[dict]:
	"""Return Employee Checkin records that were skipped by HRMS."""
	filters = {
		"skip_auto_attendance": 1,
		"attendance": ("is", "not set"),
		"offshift": 0,
	}
	if shift_type:
		filters["shift"] = shift_type
	if employee:
		filters["employee"] = employee

	start_dt = datetime.combine(getdate(from_date), datetime.min.time())
	end_dt = datetime.combine(getdate(to_date), datetime.max.time())
	filters["time"] = ("between", [start_dt, end_dt])

	return frappe.get_all(
		"Employee Checkin",
		filters=filters,
		fields=[
			"name",
			"employee",
			"employee_name",
			"shift_start",
			"shift_end",
			"shift_actual_start",
			"shift_actual_end",
			"log_type",
			"time",
			"shift",
			"device_id",
			"overtime_type",
		],
		order_by="employee, time",
	)


def _get_submitted_attendance(employee: str, attendance_date) -> dict | None:
	records = frappe.get_all(
		"Attendance",
		filters={
			"employee": employee,
			"attendance_date": attendance_date,
			"docstatus": 1,
		},
		fields=["name", "status"],
		limit=1,
	)
	return records[0] if records else None


def _is_auto_marked_absent(attendance: dict) -> bool:
	"""Check if an attendance record is auto-marked Absent created by HRMS."""
	if attendance.status != "Absent":
		return False

	# Check if there are linked checkins
	has_linked_checkin = frappe.db.exists(
		"Employee Checkin", {"attendance": attendance.name}
	)
	
	# If checkins are linked, check if they were skipped initially
	if has_linked_checkin:
		# Check if any linked checkins had skip_auto_attendance flag set
		skipped_checkins = frappe.db.count(
			"Employee Checkin",
			{
				"attendance": attendance.name,
				"skip_auto_attendance": 1
			}
		)
		# If there were skipped checkins, allow update
		# Otherwise, this is a normal absent that shouldn't be changed
		if skipped_checkins > 0:
			return True
		return False

	# Check for auto-marked comment
	has_comment = frappe.db.exists(
		"Comment",
		{
			"reference_doctype": "Attendance",
			"reference_name": attendance.name,
			"content": ("like", "%missing Employee Checkins%"),
		},
	)
	return bool(has_comment)


def _row(
	employee: str,
	employee_name: str,
	date,
	checkins: list[str],
	attendance: str | None,
	status: str,
) -> dict:
	return {
		"employee": employee,
		"employee_name": employee_name,
		"date": str(date),
		"checkins": len(checkins),
		"attendance": attendance or "",
		"status": status,
	}
