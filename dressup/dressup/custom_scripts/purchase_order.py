"""
Purchase Order – Role-Based Approval hooks and whitelisted methods.

Flow:
  Submit → status set to "Pending" → PO Approver notified
  PO Approver can: Approve or Reject (with mandatory reason)

Role required: "PO Approver"
"""

import frappe
from frappe import _
from frappe.utils import now_datetime


# ─────────────────────────────────────────────────────────────────────────────
# Hook: on_submit
# ─────────────────────────────────────────────────────────────────────────────

def notify_approvers_on_submit(doc, method=None):
	"""
	Called on Purchase Order on_submit.
	Sets approval status to Pending and notifies all PO Approver users.
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
	"""Approve the Purchase Order. Restricted to PO Approver role."""
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
	"""Reject the Purchase Order. Restricted to PO Approver role."""
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
# Internal helpers
# ─────────────────────────────────────────────────────────────────────────────

def _assert_po_approver_role():
	"""Throw PermissionError if current user does not have PO Approver role."""
	if "PO Approver" not in frappe.get_roles(frappe.session.user):
		frappe.throw(
			_("You do not have permission to perform this action. "
			  "The 'PO Approver' role is required."),
			frappe.PermissionError,
		)


def _get_po_approver_users():
	"""Return list of user emails who have the PO Approver role."""
	return frappe.get_all(
		"Has Role",
		filters={"role": "PO Approver", "parenttype": "User"},
		pluck="parent",
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
