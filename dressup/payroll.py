import frappe

# Register total_late_entries and frappe in HRMS evaluation context
try:
	from hrms.payroll.utils import COMPONENT_EVAL_GLOBALS, SALARY_SLIP_EVAL_DEFAULTS

	SALARY_SLIP_EVAL_DEFAULTS["total_late_entries"] = 0
	COMPONENT_EVAL_GLOBALS["frappe"] = frappe
except ImportError:
	pass



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
