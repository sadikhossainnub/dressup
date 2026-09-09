import frappe


def calculate_late_entries(doc, method=None):
	"""
	Calculates total submitted late entry attendances for the employee
	within the Salary Slip payroll period (start_date to end_date).
	"""
	if not doc.employee or not doc.start_date or not doc.end_date:
		doc.total_late_entries = 0
		return

	count = frappe.db.count(
		"Attendance",
		filters={
			"employee": doc.employee,
			"late_entry": 1,
			"attendance_date": ["between", [doc.start_date, doc.end_date]],
			"docstatus": 1,
		},
	)

	doc.total_late_entries = count
