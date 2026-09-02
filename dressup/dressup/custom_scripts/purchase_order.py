"""
Purchase Order – Dynamic Role-Based Approval hooks and whitelisted methods.

Flow:
  Submit → status set to "Pending" → Configured PO Approvers notified
  Allowed Approvers can: Approve or Reject (with mandatory reason)

Roles required: Configured in DressUp Settings -> PO Approval Roles (default: "PO Approver")
"""

import frappe
from frappe import _
from frappe.utils import now_datetime


@frappe.whitelist()
def get_po_approver_roles():
	"""
	Return list of role names configured in Dressup Settings for PO Approval.
	Fallback to ['PO Approver'] if no roles are configured.
	"""
	roles = []
	try:
		doc = frappe.get_doc("Dressup Settings")
		if doc.get("po_approval_roles"):
			roles = [row.role for row in doc.po_approval_roles if getattr(row, "role", None)]
	except Exception:
		pass

	if not roles:
		roles = ["PO Approver"]

	return roles


# ─────────────────────────────────────────────────────────────────────────────
# Hook: on_submit
# ─────────────────────────────────────────────────────────────────────────────

def notify_approvers_on_submit(doc, method=None):
	"""
	Called on Purchase Order on_submit.
	Sets approval status to Pending and notifies all configured PO Approver users.
	"""
	# Set status to Pending on submit
	frappe.db.set_value("Purchase Order", doc.name, "custom_po_approval_status", "Pending")
	frappe.db.commit()

	approver_users = _get_po_approver_users()
	if not approver_users:
		return

	subject = _("Purchase Order Approval Required: {0}").format(doc.name)
	message = _(
		"Purchase Order <b>{name}</b> has been submitted and requires your approval.<br><br>"
		"<b>Supplier:</b> {supplier}<br>"
		"<b>Grand Total:</b> {currency} {grand_total}<br>"
		"<b>Date:</b> {date}<br><br>"
		"<a href='/app/purchase-order/{name}'>Open Purchase Order</a>"
	).format(
		name=doc.name,
		supplier=doc.supplier,
		currency=doc.currency or "BDT",
		grand_total=frappe.utils.fmt_money(doc.grand_total, currency=doc.currency),
		date=frappe.format(doc.transaction_date, "Date"),
	)

	# Send email
	frappe.sendmail(
		recipients=approver_users,
		subject=subject,
		message=message,
	)

	# In-app notification
	try:
		for user in approver_users:
			frappe.get_doc({
				"doctype": "Notification Log",
				"subject": subject,
				"email_content": message,
				"for_user": user,
				"type": "Alert",
				"document_type": "Purchase Order",
				"document_name": doc.name,
			}).insert(ignore_permissions=True)
	except Exception:
		pass  # Notification Log may not always be available


# ─────────────────────────────────────────────────────────────────────────────
# Whitelisted methods – approval actions
# ─────────────────────────────────────────────────────────────────────────────

@frappe.whitelist()
def approve_purchase_order(po_name):
	"""Approve the Purchase Order. Restricted to configured PO Approver roles."""
	_assert_po_approver_role()

	po = frappe.get_doc("Purchase Order", po_name)
	if po.custom_po_approval_status != "Pending":
		frappe.throw(_("This Purchase Order is not pending approval."))

	frappe.db.set_value("Purchase Order", po_name, {
		"custom_po_approval_status": "Approved",
		"custom_po_approved_by": frappe.session.user,
		"custom_po_approved_on": now_datetime(),
		"custom_po_rejection_reason": "",
	})
	frappe.db.commit()

	# Notify the PO owner
	_notify_owner(po, status="Approved")

	frappe.publish_realtime("doc_update", {"doctype": "Purchase Order", "name": po_name})
	return "ok"


@frappe.whitelist()
def reject_purchase_order(po_name, reason):
	"""Reject the Purchase Order. Restricted to configured PO Approver roles."""
	_assert_po_approver_role()

	if not (reason or "").strip():
		frappe.throw(_("Rejection reason is mandatory."), frappe.MandatoryError)

	po = frappe.get_doc("Purchase Order", po_name)
	if po.custom_po_approval_status != "Pending":
		frappe.throw(_("This Purchase Order is not pending approval."))

	frappe.db.set_value("Purchase Order", po_name, {
		"custom_po_approval_status": "Rejected",
		"custom_po_approved_by": frappe.session.user,
		"custom_po_approved_on": now_datetime(),
		"custom_po_rejection_reason": reason.strip(),
	})
	frappe.db.commit()

	# Notify the PO owner about rejection
	_notify_owner(po, status="Rejected", reason=reason.strip())

	frappe.publish_realtime("doc_update", {"doctype": "Purchase Order", "name": po_name})
	return "ok"


# ─────────────────────────────────────────────────────────────────────────────
# Document Guard for Purchase Receipt and Purchase Invoice
# ─────────────────────────────────────────────────────────────────────────────

def validate_po_approval_guard(doc, method=None):
	"""
	Validate hook for Purchase Receipt and Purchase Invoice.
	Blocks saving/submitting if linked Purchase Order is not Approved.
	"""
	po_names = list({
		row.get("purchase_order")
		for row in (doc.items or [])
		if row.get("purchase_order")
	})

	if not po_names:
		return

	unapproved = []
	for po_name in po_names:
		po_status = frappe.db.get_value("Purchase Order", po_name, "custom_po_approval_status")
		if po_status != "Approved":
			unapproved.append(f"<b>{po_name}</b> (Status: <b>{po_status or 'Pending'}</b>)")

	if unapproved:
		details = "<br>".join(unapproved)
		frappe.throw(
			_(
				"Cannot process {doctype} — the following linked Purchase Order(s) are not approved yet:<br><br>"
				"{details}<br><br>Please get the Purchase Order(s) approved first."
			).format(doctype=doc.doctype, details=details),
			title=_("Purchase Order Approval Required"),
		)


# ─────────────────────────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────────────────────────

def _assert_po_approver_role():
	"""Throw PermissionError if current user does not have any of the configured PO Approver roles."""
	allowed_roles = get_po_approver_roles()
	user_roles = frappe.get_roles(frappe.session.user)

	if not any(r in user_roles for r in allowed_roles):
		roles_str = ", ".join(f"'{r}'" for r in allowed_roles)
		frappe.throw(
			_("You do not have permission to perform this action. "
			  "Required role(s): {0}.").format(roles_str),
			frappe.PermissionError,
		)


def _get_po_approver_users():
	"""Return list of user emails who have any of the configured PO Approver roles."""
	allowed_roles = get_po_approver_roles()
	if not allowed_roles:
		return []

	return frappe.get_all(
		"Has Role",
		filters={"role": ["in", allowed_roles], "parenttype": "User"},
		pluck="parent",
		distinct=True,
	)


def _notify_owner(po_doc, status, reason=None):
	"""Send email + in-app notification to the PO owner on approve/reject."""
	owner = po_doc.owner
	if not owner:
		return

	if status == "Approved":
		subject = _("Purchase Order {0} – Approved").format(po_doc.name)
		message = _(
			"Your Purchase Order <b>{name}</b> has been <b style='color:green'>Approved</b>.<br><br>"
			"<b>Approved By:</b> {by}<br>"
			"<a href='/app/purchase-order/{name}'>Open Purchase Order</a>"
		).format(name=po_doc.name, by=frappe.session.user)
	else:
		subject = _("Purchase Order {0} – Rejected").format(po_doc.name)
		message = _(
			"Your Purchase Order <b>{name}</b> has been <b style='color:red'>Rejected</b>.<br><br>"
			"<b>Rejected By:</b> {by}<br>"
			"<b>Reason:</b> {reason}<br><br>"
			"<a href='/app/purchase-order/{name}'>Open Purchase Order</a>"
		).format(name=po_doc.name, by=frappe.session.user, reason=reason or "")

	frappe.sendmail(recipients=[owner], subject=subject, message=message)

	try:
		frappe.get_doc({
			"doctype": "Notification Log",
			"subject": subject,
			"email_content": message,
			"for_user": owner,
			"type": "Alert",
			"document_type": "Purchase Order",
			"document_name": po_doc.name,
		}).insert(ignore_permissions=True)
	except Exception:
		pass


def fetch_purpose_from_material_request(doc, method=None):
	"""
	Auto-fetch Purpose (custom_purpose) from Material Request when creating or saving Purchase Order.
	- Parent level: Fetches Purpose from linked Material Request if doc.custom_purpose is empty.
	- Child level: Fetches Purpose from linked Material Request Item if item.custom_purpose is empty.
	"""
	# Fetch parent custom_purpose from Material Request if not already set
	if not doc.get("custom_purpose"):
		mr_names = [item.material_request for item in doc.get("items", []) if getattr(item, "material_request", None)]
		if mr_names:
			mr_purpose = frappe.db.get_value("Material Request", mr_names[0], "custom_purpose")
			if mr_purpose:
				doc.custom_purpose = mr_purpose

	# Fetch child custom_purpose from Material Request Item if not already set
	for item in doc.get("items", []):
		if not item.get("custom_purpose") and getattr(item, "material_request_item", None):
			mr_item_purpose = frappe.db.get_value("Material Request Item", item.material_request_item, "custom_purpose")
			if mr_item_purpose:
				item.custom_purpose = mr_item_purpose

