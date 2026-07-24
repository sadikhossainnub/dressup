# Copyright (c) 2026, Prime Technology of Bangladesh and contributors
# For license information, please see license.txt
"""
Employee → Customer creation helper.

Design notes
────────────
• Customer.mobile_no and Customer.email_id are Read-Only fetch fields that
  pull from the linked Contact record (customer_primary_contact).  They
  cannot be set directly on the Customer document.  Instead we:
    1. Insert the Customer doc (name/group/type + custom_linked_employee).
    2. Insert a Contact doc whose links table points to that Customer.
    3. Patch Customer.customer_primary_contact = contact.name so that
       Frappe's fetch mechanism populates mobile_no / email_id on the UI.

• Duplicate-name handling: if a Customer with employee.employee_name already
  exists (regardless of whether it is linked to this employee or another),
  we append the employee_id in parentheses — e.g. "John Doe (HR-EMP-00042)".
  This keeps the name human-readable while staying unique.

• Employee.custom_linked_customer is written via frappe.db.set_value so
  that Employee's own validate hooks (which run on doc.save()) are not
  triggered — Employee validation is complex and not ours to re-run.
"""

import frappe
from frappe import _


# ─────────────────────────────────────────────────────────────────────────────
# Public whitelisted API
# ─────────────────────────────────────────────────────────────────────────────

@frappe.whitelist()
def create_customer_from_employee(employee_name):
	"""
	Create a Customer record from an Employee and link the two together.

	Returns a dict::

	    {
	        "customer": "<Customer name>",
	        "message": "<human-readable status>",
	        "created": True | False   # False = already existed
	    }

	Raises frappe.PermissionError  if the caller lacks Customer create rights.
	Raises frappe.ValidationError  if employee_name is missing or not found.
	"""
	if not employee_name:
		frappe.throw(_("employee_name is required."), frappe.ValidationError)

	# ── Permission check ──────────────────────────────────────────────────────
	if not frappe.has_permission("Customer", ptype="create"):
		frappe.throw(
			_("You do not have permission to create a Customer record."),
			frappe.PermissionError,
		)

	# ── Fetch Employee ────────────────────────────────────────────────────────
	employee = frappe.get_doc("Employee", employee_name)

	# ── Idempotency: return early if already linked ───────────────────────────
	if employee.custom_linked_customer:
		existing = employee.custom_linked_customer
		return {
			"customer": existing,
			"message": _("Customer already linked: {0}").format(existing),
			"created": False,
		}

	# ── Resolve customer_name (handle duplicates) ─────────────────────────────
	base_name = (employee.employee_name or "").strip()
	if not base_name:
		frappe.throw(
			_("Employee {0} has no Full Name set. Please fill in the name first.").format(employee_name),
			frappe.ValidationError,
		)

	customer_name = _resolve_customer_name(base_name, employee.name)

	# ── Build email / phone from Employee ─────────────────────────────────────
	email = (employee.company_email or employee.personal_email or "").strip()
	phone = (employee.cell_number or "").strip()

	# ── Split name into first / last for Contact ──────────────────────────────
	name_parts = base_name.split(" ", 1)
	first_name = name_parts[0]
	last_name  = name_parts[1] if len(name_parts) > 1 else ""

	# ── Insert Customer ───────────────────────────────────────────────────────
	customer = frappe.get_doc({
		"doctype": "Customer",
		"customer_name": customer_name,
		"customer_type": "Individual",
		"customer_group": "Employee",
		# reverse link so the relationship is queryable from Customer side
		"custom_linked_employee": employee.name,
	})
	# Respect normal permission checks — do NOT use ignore_permissions=True
	customer.insert(ignore_permissions=False)

	# ── Create a linked Contact with phone + email ────────────────────────────
	contact = _create_contact(
		customer_name=customer.name,
		first_name=first_name,
		last_name=last_name,
		phone=phone,
		email=email,
	)

	# ── Link Contact as primary contact on Customer ───────────────────────────
	# Use db.set_value to avoid re-running Customer validation side-effects
	frappe.db.set_value(
		"Customer",
		customer.name,
		"customer_primary_contact",
		contact.name,
		update_modified=False,
	)

	# ── Back-link Employee.custom_linked_customer ─────────────────────────────
	# db.set_value bypasses Employee's own validate hooks intentionally —
	# Employee validation (leave policies, salary structures, etc.) should not
	# fire just because we're recording a CRM link.
	frappe.db.set_value(
		"Employee",
		employee.name,
		"custom_linked_customer",
		customer.name,
		update_modified=False,
	)

	frappe.db.commit()

	return {
		"customer": customer.name,
		"message": _("Customer {0} created and linked successfully.").format(customer.name),
		"created": True,
	}


# ─────────────────────────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────────────────────────

def _resolve_customer_name(base_name, employee_id):
	"""
	Return a Customer name that does not collide with an existing one.

	If ``base_name`` is already taken, append the employee_id in parentheses.
	The employee_id-qualified name is assumed to be unique because employee IDs
	are unique across the system.
	"""
	if not frappe.db.exists("Customer", {"customer_name": base_name}):
		return base_name
	# Collision: qualify with employee_id
	qualified = "{0} ({1})".format(base_name, employee_id)
	return qualified


def _create_contact(customer_name, first_name, last_name, phone, email):
	"""
	Insert a Contact document linked to *customer_name*.

	The Contact's ``links`` child table must have an entry pointing to the
	Customer so that ERPNext recognises it as a Customer contact.
	The optional phone and email rows are only added when non-empty.
	"""
	contact_doc = frappe.get_doc({
		"doctype": "Contact",
		"first_name": first_name,
		"last_name": last_name,
		"links": [
			{
				"link_doctype": "Customer",
				"link_name": customer_name,
			}
		],
	})

	# Phone — stored in the phone_nos child table
	if phone:
		contact_doc.append("phone_nos", {
			"phone": phone,
			"is_primary_mobile_no": 1,
		})

	# Email — stored in the email_ids child table
	if email:
		contact_doc.append("email_ids", {
			"email_id": email,
			"is_primary": 1,
		})

	contact_doc.insert(ignore_permissions=False)
	return contact_doc
