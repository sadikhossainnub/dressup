"""
Discount Approval Guard
=======================
Blocks Sales Invoice and Delivery Note creation (on validate, which runs
on both Save and Submit) when the source Sales Order has a discount pending
approval or has been rejected.

Field name investigation results
---------------------------------
- Sales Invoice Item  → 'sales_order'          (confirmed from sales_invoice_item.json)
- Delivery Note Item  → 'against_sales_order'  (confirmed from delivery_note_item.json)

If a document has items linked to MULTIPLE Sales Orders, ALL linked SOs are checked.
If ANY SO is in a blocking state, the error is thrown listing all blocking SOs.
Standalone documents with no SO links are skipped entirely.
"""

import frappe
from frappe import _


# Map each parent doctype to the fieldname in its items table that holds the SO name
_SO_FIELD = {
	"Sales Invoice": "sales_order",
	"Delivery Note": "against_sales_order",
}

_ALLOWED_STATUSES = frozenset(["Not Required", "Approved"])


def block_if_not_approved(doc, method=None):
	"""
	Validate hook for Sales Invoice and Delivery Note.
	Raises frappe.ValidationError if the source SO has an un-approved extra discount.
	"""
	so_field = _SO_FIELD.get(doc.doctype)
	if not so_field:
		return  # safety guard — should never happen

	# Collect distinct, non-empty SO names from items
	so_names = list({
		row.get(so_field)
		for row in (doc.items or [])
		if row.get(so_field)
	})

	if not so_names:
		# Standalone document (no SO link) — skip entirely
		return

	blocking = []

	for so_name in so_names:
		data = frappe.db.get_value(
			"Sales Order",
			so_name,
			["custom_approval_status", "custom_approval_reason"],
			as_dict=True,
		)
		if not data:
			continue  # SO deleted or inaccessible — skip

		status = data.get("custom_approval_status") or "Not Required"

		if status not in _ALLOWED_STATUSES:
			reason = (data.get("custom_approval_reason") or "").replace("\n", "; ")
			blocking.append(
				f"<b>{so_name}</b> — Status: <b>{status}</b><br>"
				f"Reason: {frappe.utils.escape_html(reason)}"
			)

	if blocking:
		details = "<br><br>".join(blocking)
		frappe.throw(
			_(
				"Cannot create {doctype} — the following linked Sales Order(s) have a "
				"discount pending approval or have been rejected:<br><br>{details}<br><br>"
				"Please get the discount approved before proceeding."
			).format(doctype=doc.doctype, details=details),
			title=_("Discount Approval Required"),
		)
