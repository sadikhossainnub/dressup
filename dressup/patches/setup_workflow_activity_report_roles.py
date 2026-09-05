import frappe


def execute():
	"""
	Patch to ensure required Manager roles exist in database
	and are linked to Workflow State Activity Report.
	"""
	manager_roles = [
		"Fashion Designer Manager",
		"Production Manager",
		"Quality Manager",
		"Sales Manager",
		"Purchase Manager",
		"Stock Manager",
		"HR Manager",
	]

	for r in manager_roles:
		if not frappe.db.exists("Role", r):
			role_doc = frappe.get_doc({
				"doctype": "Role",
				"role_name": r,
				"desk_access": 1,
			})
			role_doc.insert(ignore_permissions=True)

	report_name = "Workflow State Activity Report"
	if frappe.db.exists("Report", report_name):
		report_doc = frappe.get_doc("Report", report_name)
		existing_roles = [d.role for d in report_doc.roles]
		all_roles = ["System Manager"] + manager_roles

		updated = False
		for r in all_roles:
			if r not in existing_roles:
				report_doc.append("roles", {"role": r})
				updated = True

		if updated:
			report_doc.save(ignore_permissions=True)
	else:
		frappe.reload_doc("dressup", "report", "workflow_state_activity_report", force=True)
