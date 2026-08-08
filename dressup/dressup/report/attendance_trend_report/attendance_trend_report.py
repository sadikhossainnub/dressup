# Copyright (c) 2026, Prime Technology of Bangladesh and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, cstr


def execute(filters=None):
	if not filters:
		filters = {}

	group_by = filters.get("group_by") or "Employee"
	columns = get_columns(group_by)
	data = get_data(filters, group_by)
	return columns, data


# ---------------------------------------------------------------------------
# Columns
# ---------------------------------------------------------------------------

def get_columns(group_by):
	"""Return columns based on grouping dimension."""

	# Label for the first identity column
	group_labels = {
		"Employee":   (_("Employee"),   "employee",   "Link", "Employee",   160),
		"Department": (_("Department"), "department", "Link", "Department", 160),
		"Month":      (_("Month"),      "period",     "Data", None,          120),
		"Week":       (_("Week"),       "period",     "Data", None,          140),
	}

	label, fname, ftype, opts, width = group_labels.get(group_by, group_labels["Employee"])

	cols = [
		{
			"label": label,
			"fieldname": fname,
			"fieldtype": ftype,
			"options": opts,
			"width": width,
		}
	]

	# For Employee / Department groupings add descriptive sub-columns
	if group_by == "Employee":
		cols += [
			{
				"label": _("Employee Name"),
				"fieldname": "employee_name",
				"fieldtype": "Data",
				"width": 160,
			},
			{
				"label": _("Department"),
				"fieldname": "department",
				"fieldtype": "Link",
				"options": "Department",
				"width": 140,
			},
			{
				"label": _("Designation"),
				"fieldname": "designation",
				"fieldtype": "Data",
				"width": 130,
			},
		]

	elif group_by == "Department":
		cols += [
			{
				"label": _("No. of Employees"),
				"fieldname": "employee_count",
				"fieldtype": "Int",
				"width": 130,
			}
		]

	# ---- Common metric columns ------------------------------------------------
	cols += [
		{
			"label": _("Total Working Days"),
			"fieldname": "total_working_days",
			"fieldtype": "Int",
			"width": 140,
		},
		{
			"label": _("Present Days"),
			"fieldname": "present_days",
			"fieldtype": "Float",
			"width": 110,
		},
		{
			"label": _("Absent Days"),
			"fieldname": "absent_days",
			"fieldtype": "Float",
			"width": 110,
		},
		{
			"label": _("Half Days"),
			"fieldname": "half_days",
			"fieldtype": "Float",
			"width": 100,
		},
		{
			"label": _("On Leave Days"),
			"fieldname": "on_leave_days",
			"fieldtype": "Float",
			"width": 120,
		},
		{
			"label": _("Late Arrivals"),
			"fieldname": "late_days",
			"fieldtype": "Int",
			"width": 110,
		},
		{
			"label": _("Leave Breakdown"),
			"fieldname": "leave_breakdown",
			"fieldtype": "Data",
			"width": 200,
		},
		{
			"label": _("Attendance %"),
			"fieldname": "attendance_percentage",
			"fieldtype": "Percent",
			"width": 120,
		},
	]

	return cols


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------

def get_data(filters, group_by):
	raw = fetch_attendance_rows(filters)

	if group_by == "Employee":
		return aggregate_by_employee(raw, filters)
	elif group_by == "Department":
		return aggregate_by_department(raw, filters)
	elif group_by == "Month":
		return aggregate_by_period(raw, filters, period_type="month")
	elif group_by == "Week":
		return aggregate_by_period(raw, filters, period_type="week")
	return []


# ---------------------------------------------------------------------------
# SQL fetch
# ---------------------------------------------------------------------------

def fetch_attendance_rows(filters):
	conditions = build_conditions(filters)

	return frappe.db.sql(
		f"""
		SELECT
			att.name            AS name,
			att.employee        AS employee,
			att.employee_name   AS employee_name,
			att.department      AS department,
			att.designation     AS designation,
			att.attendance_date AS attendance_date,
			att.status          AS status,
			att.leave_type      AS leave_type,
			att.late_entry      AS late_entry,
			att.shift           AS shift,
			att.attendance_request AS attendance_request
		FROM
			`tabAttendance` att
		WHERE
			att.docstatus = 1
			{conditions}
		ORDER BY
			att.attendance_date ASC, att.employee ASC
		""",
		{
			"company":    filters.get("company"),
			"from_date":  filters.get("from_date"),
			"to_date":    filters.get("to_date"),
			"department": filters.get("department"),
			"employee":   filters.get("employee"),
			"status":     filters.get("status"),
			"shift":      filters.get("shift"),
			"device_id":  filters.get("attendance_device_id"),
		},
		as_dict=True,
	)


def build_conditions(filters):
	parts = []

	if filters.get("company"):
		parts.append("AND att.company = %(company)s")
	if filters.get("from_date"):
		parts.append("AND att.attendance_date >= %(from_date)s")
	if filters.get("to_date"):
		parts.append("AND att.attendance_date <= %(to_date)s")
	if filters.get("department"):
		parts.append("AND att.department = %(department)s")
	if filters.get("employee"):
		parts.append("AND att.employee = %(employee)s")
	if filters.get("status"):
		parts.append("AND att.status = %(status)s")
	if filters.get("shift"):
		parts.append("AND att.shift = %(shift)s")
	if filters.get("attendance_device_id"):
		parts.append(
			"AND att.employee IN ("
			"  SELECT name FROM `tabEmployee` "
			"  WHERE attendance_device_id = %(device_id)s"
			")"
		)

	return " ".join(parts)


# ---------------------------------------------------------------------------
# Working-days helper
# ---------------------------------------------------------------------------

def get_working_days(filters):
	"""Count distinct attendance dates (submitted records) within the filter range."""
	conds = []
	vals = {}

	if filters.get("company"):
		conds.append("company = %(company)s")
		vals["company"] = filters["company"]
	if filters.get("from_date"):
		conds.append("attendance_date >= %(from_date)s")
		vals["from_date"] = filters["from_date"]
	if filters.get("to_date"):
		conds.append("attendance_date <= %(to_date)s")
		vals["to_date"] = filters["to_date"]

	where = ("WHERE " + " AND ".join(conds) + " AND docstatus = 1") if conds else "WHERE docstatus = 1"
	result = frappe.db.sql(
		f"SELECT COUNT(DISTINCT attendance_date) FROM `tabAttendance` {where}", vals
	)
	return (result[0][0] or 0) if result else 0


# ---------------------------------------------------------------------------
# Leave breakdown helper
# ---------------------------------------------------------------------------

def build_leave_breakdown(leave_counter):
	"""Turn {'Annual Leave': 3, 'Sick Leave': 1} → 'Annual Leave: 3, Sick Leave: 1'."""
	if not leave_counter:
		return ""
	return ", ".join(f"{lt}: {cnt}" for lt, cnt in sorted(leave_counter.items()))


# ---------------------------------------------------------------------------
# Metric accumulator initialiser
# ---------------------------------------------------------------------------

def _empty_metrics():
	return {
		"present_days":    0.0,
		"absent_days":     0.0,
		"half_days":       0.0,
		"on_leave_days":   0.0,
		"late_days":       0,
		"leave_types":     {},   # leave_type → count
	}


def _accumulate(metrics, row):
	status = row.get("status") or ""
	if status == "Present":
		metrics["present_days"] += 1
	elif status == "Absent":
		metrics["absent_days"] += 1
	elif status == "Half Day":
		metrics["half_days"] += 0.5
		metrics["present_days"] += 0.5
	elif status == "On Leave":
		metrics["on_leave_days"] += 1
		lt = row.get("leave_type") or "—"
		metrics["leave_types"][lt] = metrics["leave_types"].get(lt, 0) + 1

	if row.get("late_entry"):
		metrics["late_days"] += 1


def _attendance_pct(present, working_days):
	if not working_days:
		return 0.0
	return flt(present / working_days * 100, 2)


# ---------------------------------------------------------------------------
# Aggregation: by Employee
# ---------------------------------------------------------------------------

def aggregate_by_employee(rows, filters):
	working_days = get_working_days(filters)
	buckets = {}   # employee → metrics dict

	for row in rows:
		emp = row["employee"]
		if emp not in buckets:
			buckets[emp] = {
				**_empty_metrics(),
				"employee":      emp,
				"employee_name": row.get("employee_name") or "",
				"department":    row.get("department") or "",
				"designation":   row.get("designation") or "",
			}
		_accumulate(buckets[emp], row)

	data = []
	for emp, m in sorted(buckets.items(), key=lambda x: x[1]["employee_name"]):
		eff_present = m["present_days"]
		data.append({
			"employee":             emp,
			"employee_name":        m["employee_name"],
			"department":           m["department"],
			"designation":          m["designation"],
			"total_working_days":   working_days,
			"present_days":         eff_present,
			"absent_days":          m["absent_days"],
			"half_days":            m["half_days"],
			"on_leave_days":        m["on_leave_days"],
			"late_days":            m["late_days"],
			"leave_breakdown":      build_leave_breakdown(m["leave_types"]),
			"attendance_percentage": _attendance_pct(eff_present, working_days),
		})
	return data


# ---------------------------------------------------------------------------
# Aggregation: by Department
# ---------------------------------------------------------------------------

def aggregate_by_department(rows, filters):
	working_days = get_working_days(filters)
	buckets = {}   # department → metrics
	employees = {} # department → set of employee ids

	for row in rows:
		dept = row.get("department") or "—"
		if dept not in buckets:
			buckets[dept] = _empty_metrics()
			employees[dept] = set()
		employees[dept].add(row["employee"])
		_accumulate(buckets[dept], row)

	data = []
	for dept, m in sorted(buckets.items()):
		emp_count = len(employees[dept])
		eff_present = m["present_days"]
		total_wd = working_days * emp_count if emp_count else working_days
		data.append({
			"department":           dept,
			"employee_count":       emp_count,
			"total_working_days":   total_wd,
			"present_days":         eff_present,
			"absent_days":          m["absent_days"],
			"half_days":            m["half_days"],
			"on_leave_days":        m["on_leave_days"],
			"late_days":            m["late_days"],
			"leave_breakdown":      build_leave_breakdown(m["leave_types"]),
			"attendance_percentage": _attendance_pct(eff_present, total_wd),
		})
	return data


# ---------------------------------------------------------------------------
# Aggregation: by Period (Month / Week)
# ---------------------------------------------------------------------------

def aggregate_by_period(rows, filters, period_type="month"):
	buckets  = {}
	employees_per_period = {}

	for row in rows:
		att_date = row["attendance_date"]
		if period_type == "month":
			period_key = att_date.strftime("%Y-%m") if hasattr(att_date, "strftime") else cstr(att_date)[:7]
			period_label = att_date.strftime("%B %Y") if hasattr(att_date, "strftime") else period_key
		else:
			# ISO week: year-Www
			if hasattr(att_date, "isocalendar"):
				iso = att_date.isocalendar()
				period_key = f"{iso[0]}-W{iso[1]:02d}"
				period_label = f"Week {iso[1]:02d}, {iso[0]}"
			else:
				period_key = cstr(att_date)[:10]
				period_label = period_key

		if period_key not in buckets:
			buckets[period_key] = {**_empty_metrics(), "label": period_label}
			employees_per_period[period_key] = set()

		employees_per_period[period_key].add(row["employee"])
		_accumulate(buckets[period_key], row)

	data = []
	for period_key in sorted(buckets.keys()):
		m = buckets[period_key]
		emp_count = len(employees_per_period[period_key])
		eff_present = m["present_days"]

		# Estimate working days in period as count of distinct attendance dates
		dates_in_period = frappe.db.sql(
			"""
			SELECT COUNT(DISTINCT attendance_date)
			FROM `tabAttendance`
			WHERE docstatus = 1
			  AND attendance_date BETWEEN %(from_date)s AND %(to_date)s
			""",
			{"from_date": filters.get("from_date"), "to_date": filters.get("to_date")},
		)
		period_working_days = (dates_in_period[0][0] or 1) * emp_count

		data.append({
			"period":               m["label"],
			"total_working_days":   period_working_days,
			"present_days":         eff_present,
			"absent_days":          m["absent_days"],
			"half_days":            m["half_days"],
			"on_leave_days":        m["on_leave_days"],
			"late_days":            m["late_days"],
			"leave_breakdown":      build_leave_breakdown(m["leave_types"]),
			"attendance_percentage": _attendance_pct(eff_present, period_working_days),
		})
	return data
