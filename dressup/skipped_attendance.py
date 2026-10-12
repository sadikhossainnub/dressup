# Copyright (c) 2026, Prime Technology of Bangladesh and contributors
# For license information, please see license.txt

"""Recheck / fix Employee Checkins whose *skip_auto_attendance* flag was set
because a duplicate-Absent attendance already existed when HRMS tried to
mark attendance from late-arriving biometric punches.

Usage (bench console):
    from dressup.skipped_attendance import recheck_skipped_attendance
    recheck_skipped_attendance("Day Shift", "2026-10-01", "2026-10-12", dry_run=1)

Usage (client):
    Called from the "Recheck Skipped Attendance" button on the Shift Type form.
"""

from __future__ import annotations

from datetime import datetime
from itertools import groupby

import frappe
from frappe import _
from frappe.utils import getdate


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

@frappe.whitelist()
def recheck_skipped_attendance(
	shift_type: str,
	from_date: str,
	to_date: str,
	employee: str | None = None,
	dry_run: int | bool = 1,
) -> dict:
	"""Find skipped checkins, optionally cancel auto-Absent attendance and
	re-run ``process_auto_attendance`` so HRMS creates the correct record.

	Returns a dict with keys:
	    dry_run, to_fix, untouched, failed, process_message
	"""
	dry_run = int(dry_run)

	shift = frappe.get_doc("Shift Type", shift_type)
	shift.check_permission("write")

	if shift.has_incorrect_shift_config():
		frappe.throw(
			_(
				"Shift Type {0} has incomplete auto-attendance configuration. "
				"Please set 'Enable Auto Attendance', 'Process Attendance After' "
				"and 'Last Sync of Checkin' before running this tool."
			).format(frappe.bold(shift_type))
		)

	# ------------------------------------------------------------------
	# 1. Fetch skipped checkins
	# ------------------------------------------------------------------
	logs = _get_skipped_checkins(shift_type, from_date, to_date, employee)
	if not logs:
		return {
			"dry_run": dry_run,
			"to_fix": [],
			"untouched": [],
			"failed": [],
			"process_message": _("No skipped checkins found for the given filters."),
		}

	# ------------------------------------------------------------------
	# 2. Group by (employee, attendance_date)
	# ------------------------------------------------------------------
	group_key = lambda log: (log.employee, getdate(log.shift_start))
	sorted_logs = sorted(logs, key=group_key)

	to_fix: list[dict] = []
	untouched: list[dict] = []
	failed: list[dict] = []

	for (emp, att_date), group_iter in groupby(sorted_logs, key=group_key):
		group_logs = list(group_iter)
		emp_name = group_logs[0].employee_name
		checkin_names = [l.name for l in group_logs]

		# Find submitted attendance for this employee + date
		attendance = _get_submitted_attendance(emp, att_date)
		if not attendance:
			# No submitted attendance at all — nothing to cancel.
			# The checkins can simply be un-skipped so the next
			# process_auto_attendance picks them up.
			to_fix.append(
				_row(emp, emp_name, att_date, checkin_names, None, "No Attendance (will un-skip)")
			)
			if not dry_run:
				_reset_skip_flag(checkin_names)
			continue

		if not _is_auto_marked_absent(attendance):
			# Present / Half Day / On Leave / manual Absent — do not touch
			untouched.append(
				_row(
					emp, emp_name, att_date, checkin_names,
					attendance.name, attendance.status,
				)
			)
			continue

		# This is an auto-marked Absent that we should fix
		to_fix.append(
			_row(emp, emp_name, att_date, checkin_names, attendance.name, "Auto-Absent → will cancel")
		)

		if not dry_run:
			try:
				frappe.db.savepoint("recheck_att")
				att_doc = frappe.get_doc("Attendance", attendance.name)
				att_doc.flags.ignore_permissions = True
				att_doc.cancel()
			except frappe.ValidationError as exc:
				frappe.db.rollback(save_point="recheck_att")
				frappe.clear_messages()
				failed.append(
					_row(
						emp, emp_name, att_date, checkin_names,
						attendance.name, str(exc),
					)
				)
				continue

			# Cancel succeeded — reset the skip flag on checkins
			_reset_skip_flag(checkin_names)

	# ------------------------------------------------------------------
	# 3. Re-run process_auto_attendance (only when not dry_run)
	# ------------------------------------------------------------------
	process_message = ""
	if not dry_run:
		if not frappe.flags.in_test:
			frappe.db.commit()  # nosemgrep
		# Reload shift to pick up latest settings
		shift.reload()
		process_message = shift.process_auto_attendance(is_manually_triggered=True) or _(
			"Attendance has been marked as per employee check-ins."
		)
	else:
		if to_fix:
			process_message = _(
				"{0} group(s) can be fixed. Un-check 'Preview only' and run again to apply."
			).format(len(to_fix))
		else:
			process_message = _("Nothing to fix.")

	return {
		"dry_run": dry_run,
		"to_fix": to_fix,
		"untouched": untouched,
		"failed": failed,
		"process_message": process_message,
	}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_skipped_checkins(
	shift_type: str,
	from_date: str,
	to_date: str,
	employee: str | None = None,
) -> list[dict]:
	"""Return Employee Checkin records that were skipped by HRMS."""
	filters = {
		"shift": shift_type,
		"skip_auto_attendance": 1,
		"attendance": ("is", "not set"),
		"offshift": 0,
		"shift_start": (
			"between",
			[
				datetime.combine(getdate(from_date), datetime.min.time()),
				datetime.combine(getdate(to_date), datetime.max.time()),
			],
		),
	}
	if employee:
		filters["employee"] = employee

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
	"""Return the first submitted (docstatus=1) attendance for the employee
	on the given date, if any."""
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
	"""Check if an attendance record is an auto-marked Absent created by
	HRMS's ``mark_absent_for_dates_with_no_attendance``.

	Conditions:
	  1. status == "Absent"
	  2. No Employee Checkin is linked to this attendance
	  3. A Comment exists with the telltale HRMS message
	"""
	if attendance.status != "Absent":
		return False

	# Any checkin linked?
	has_linked_checkin = frappe.db.exists(
		"Employee Checkin", {"attendance": attendance.name}
	)
	if has_linked_checkin:
		return False

	# HRMS comment present?
	has_comment = frappe.db.exists(
		"Comment",
		{
			"reference_doctype": "Attendance",
			"reference_name": attendance.name,
			"content": ("like", "%missing Employee Checkins%"),
		},
	)
	return bool(has_comment)


def _reset_skip_flag(checkin_names: list[str]) -> None:
	"""Set skip_auto_attendance = 0 on the given checkins without touching
	modified timestamps."""
	if not checkin_names:
		return
	EmployeeCheckin = frappe.qb.DocType("Employee Checkin")
	(
		frappe.qb.update(EmployeeCheckin)
		.set("skip_auto_attendance", 0)
		.set("attendance", None)
		.where(EmployeeCheckin.name.isin(checkin_names))
	).run()


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
