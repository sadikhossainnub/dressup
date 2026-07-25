"""
Sales Order – Discount Approval hooks and whitelisted methods.

Checks TWO levels of discount:

1. ROW-LEVEL  — each item's discount_percentage vs what the Pricing Rule engine
                would normally apply (get_pricing_rule_for_item).
                No Pricing Rule match → standard = 0, any manual discount is extra.

2. HEADER-LEVEL — additional_discount_percentage (% on net/grand total) and
                  discount_amount (fixed ৳ on net/grand total).
                  Any non-zero value in either field is treated as extra discount
                  because there is no ERPNext-standard Pricing Rule that governs
                  these header fields — they are always manually entered.

Tolerance: 0.01 percentage points for row-level comparison.
Header-level: any value > 0 is flagged (no tolerance — it's always manual).
Flagged for reviewer: adjust DISCOUNT_TOLERANCE if a looser threshold is needed.
"""

import frappe
from frappe import _
from frappe.utils import flt, now_datetime

DISCOUNT_TOLERANCE = 0.01  # percentage points — for row-level comparison only


# ─────────────────────────────────────────────────────────────────────────────
# PART 3 – validate hook
# ─────────────────────────────────────────────────────────────────────────────

def check_extra_discount(doc, method=None):
	"""
	Called on Sales Order validate.
	Checks both row-level item discounts and header-level additional discount.
	Sets approval fields accordingly. Does NOT block submission.
	"""
	from erpnext.accounts.doctype.pricing_rule.pricing_rule import get_pricing_rule_for_item

	flagged_lines = []

	# ── 1. ROW-LEVEL: per-item discount_percentage ───────────────────────
	for row in doc.items:
		if not row.item_code:
			continue

		row_discount = flt(row.discount_percentage)

		# Build the args dict that get_pricing_rule_for_item expects
		pr_args = frappe._dict({
			"doctype": doc.doctype + " Item",
			"name": row.name,
			"parent": doc.name,
			"parenttype": doc.doctype,
			"child_docname": row.name,
			"item_code": row.item_code,
			"item_group": frappe.get_cached_value("Item", row.item_code, "item_group") or "",
			"brand": frappe.get_cached_value("Item", row.item_code, "brand") or "",
			"transaction_type": "selling",
			"price_list": doc.selling_price_list,
			"price_list_currency": doc.price_list_currency,
			"plc_conversion_rate": flt(doc.plc_conversion_rate) or 1,
			"conversion_rate": flt(doc.conversion_rate) or 1,
			"currency": doc.currency,
			"customer": doc.customer,
			"customer_group": frappe.get_cached_value("Customer", doc.customer, "customer_group") if doc.customer else None,
			"territory": frappe.get_cached_value("Customer", doc.customer, "territory") if doc.customer else None,
			"supplier": None,
			"supplier_group": None,
			"qty": flt(row.qty),
			"stock_qty": flt(row.stock_qty) or flt(row.qty),
			"uom": row.uom,
			"stock_uom": row.stock_uom or row.uom,
			"price_list_rate": flt(row.price_list_rate),
			"transaction_date": doc.transaction_date,
			"company": doc.company,
			"campaign": doc.get("campaign"),
			"coupon_code": doc.get("coupon_code"),
			"ignore_pricing_rule": 0,
			"is_free_item": 0,
			"is_return": 0,
			# Don't pass existing pricing_rules so we get a fresh evaluation
			"pricing_rules": None,
		})

		try:
			pr_result = get_pricing_rule_for_item(pr_args)
		except Exception:
			frappe.log_error(
				frappe.get_traceback(),
				f"Discount check: pricing rule lookup failed for item {row.item_code} on {doc.name}"
			)
			continue

		standard_discount = flt(pr_result.get("discount_percentage") or 0)
		applied_rule_name = None

		if pr_result.get("pricing_rules"):
			import json as _json
			try:
				rules_list = _json.loads(pr_result.get("pricing_rules"))
				if rules_list:
					applied_rule_name = rules_list[0]
			except Exception:
				pass

		if row_discount - standard_discount > DISCOUNT_TOLERANCE:
			rule_info = f" (Pricing Rule: {applied_rule_name})" if applied_rule_name else " (No Pricing Rule)"
			flagged_lines.append(
				f"Row {row.idx} – {row.item_code}: "
				f"{row_discount:.2f}% given vs {standard_discount:.2f}% standard{rule_info}"
			)

	# ── 2. HEADER-LEVEL: additional_discount_percentage ──────────────────
	# This is the "Additional Discount %" field on the SO form (applied on
	# Net Total or Grand Total). Any non-zero value is always manual — no
	# Pricing Rule governs it — so it always requires approval.
	additional_disc_pct = flt(doc.get("additional_discount_percentage"))
	if additional_disc_pct > 0:
		apply_on = doc.get("apply_discount_on") or "Grand Total"
		flagged_lines.append(
			f"Additional Discount %: {additional_disc_pct:.2f}% on {apply_on} (header-level)"
		)

	# ── 3. HEADER-LEVEL: discount_amount (fixed ৳ amount) ────────────────
	# The fixed "Discount Amount" field on the SO form.
	discount_amount = flt(doc.get("discount_amount"))
	if discount_amount > 0:
		apply_on = doc.get("apply_discount_on") or "Grand Total"
		flagged_lines.append(
			f"Additional Discount Amount: {doc.get('currency', '')} {discount_amount:,.2f} on {apply_on} (header-level)"
		)

	# ── Set approval fields ───────────────────────────────────────────────
	if flagged_lines:
		doc.custom_has_extra_discount = 1
		# Preserve Approved/Rejected status if already actioned — don't reset
		if doc.custom_approval_status not in ("Approved", "Rejected"):
			doc.custom_approval_status = "Pending"
		doc.custom_approval_reason = "\n".join(flagged_lines)
	else:
		doc.custom_has_extra_discount = 0
		# Fully clear if no discount found and not yet approved/rejected
		if doc.custom_approval_status not in ("Approved", "Rejected"):
			doc.custom_approval_status = "Not Required"
			doc.custom_approval_reason = ""


# ─────────────────────────────────────────────────────────────────────────────
# PART 3 – on_submit hook: notify Discount Approvers
# ─────────────────────────────────────────────────────────────────────────────

def notify_approvers_on_submit(doc, method=None):
	"""
	After Sales Order is submitted, if approval is pending send a
	Frappe Notification to all users with the 'Discount Approver' role.
	"""
	if doc.custom_approval_status != "Pending":
		return

	approver_users = _get_discount_approver_users()
	if not approver_users:
		return

	subject = _("Discount Approval Required: {0}").format(doc.name)
	message = _(
		"Sales Order <b>{name}</b> has been submitted and requires discount approval.<br><br>"
		"<b>Reason:</b><br>{reason}<br><br>"
		"<a href='/app/sales-order/{name}'>Open Sales Order</a>"
	).format(name=doc.name, reason=(doc.custom_approval_reason or "").replace("\n", "<br>"))

	for user in approver_users:
		frappe.sendmail(
			recipients=[user],
			subject=subject,
			message=message,
			delayed=False,
		)

	# Also create a Frappe Notification document for in-app alert
	try:
		for user in approver_users:
			frappe.get_doc({
				"doctype": "Notification Log",
				"subject": subject,
				"email_content": message,
				"for_user": user,
				"type": "Alert",
				"document_type": "Sales Order",
				"document_name": doc.name,
			}).insert(ignore_permissions=True)
	except Exception:
		pass  # Notification Log may not always be available

	# Log the initial Pending entry
	_insert_approval_log(
		sales_order=doc.name,
		approval_status="Pending",
		item_details=doc.custom_approval_reason or "",
	)


# ─────────────────────────────────────────────────────────────────────────────
# PART 4 – Whitelisted methods for approval actions
# ─────────────────────────────────────────────────────────────────────────────

@frappe.whitelist()
def mark_under_review(sales_order_name):
	"""Set approval status to 'Under Review'. Restricted to Discount Approver role."""
	_assert_discount_approver_role()

	so = frappe.get_doc("Sales Order", sales_order_name)
	if so.custom_approval_status not in ("Pending", "Under Review"):
		frappe.throw(_("This Sales Order is not pending discount approval."))

	frappe.db.set_value("Sales Order", sales_order_name, {
		"custom_approval_status": "Under Review",
		"custom_reviewed_by": frappe.session.user,
	})
	frappe.db.commit()

	_insert_approval_log(
		sales_order=sales_order_name,
		approval_status="Under Review",
		reviewed_by=frappe.session.user,
		item_details=so.custom_approval_reason or "",
	)

	frappe.publish_realtime("doc_update", {"doctype": "Sales Order", "name": sales_order_name})
	return "ok"


@frappe.whitelist()
def approve_extra_discount(sales_order_name):
	"""Approve the extra discount. Restricted to Discount Approver role."""
	_assert_discount_approver_role()

	so = frappe.get_doc("Sales Order", sales_order_name)
	if so.custom_approval_status not in ("Pending", "Under Review"):
		frappe.throw(_("This Sales Order is not pending discount approval."))

	frappe.db.set_value("Sales Order", sales_order_name, {
		"custom_approval_status": "Approved",
		"custom_approved_by": frappe.session.user,
		"custom_approved_on": now_datetime(),
	})
	frappe.db.commit()

	_insert_approval_log(
		sales_order=sales_order_name,
		approval_status="Approved",
		approved_by=frappe.session.user,
		item_details=so.custom_approval_reason or "",
	)

	frappe.publish_realtime("doc_update", {"doctype": "Sales Order", "name": sales_order_name})
	return "ok"


@frappe.whitelist()
def reject_extra_discount(sales_order_name, reason):
	"""Reject the extra discount. Restricted to Discount Approver role."""
	_assert_discount_approver_role()

	if not (reason or "").strip():
		frappe.throw(_("Rejection reason is mandatory."), frappe.MandatoryError)

	so = frappe.get_doc("Sales Order", sales_order_name)
	if so.custom_approval_status not in ("Pending", "Under Review"):
		frappe.throw(_("This Sales Order is not pending discount approval."))

	frappe.db.set_value("Sales Order", sales_order_name, {
		"custom_approval_status": "Rejected",
		"custom_rejection_reason": reason.strip(),
		"custom_approved_by": frappe.session.user,
		"custom_approved_on": now_datetime(),
	})
	frappe.db.commit()

	_insert_approval_log(
		sales_order=sales_order_name,
		approval_status="Rejected",
		approved_by=frappe.session.user,
		rejection_reason=reason.strip(),
		item_details=so.custom_approval_reason or "",
	)

	# Notify the SO owner about rejection
	_notify_owner_on_rejection(so, reason.strip())

	frappe.publish_realtime("doc_update", {"doctype": "Sales Order", "name": sales_order_name})
	return "ok"


# ─────────────────────────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────────────────────────

def _assert_discount_approver_role():
	"""Throw PermissionError if current user does not have Discount Approver role."""
	if "Discount Approver" not in frappe.get_roles(frappe.session.user):
		frappe.throw(
			_("You do not have permission to perform this action. "
			  "The 'Discount Approver' role is required."),
			frappe.PermissionError,
		)


def _get_discount_approver_users():
	"""Return list of user emails who have the Discount Approver role."""
	return frappe.get_all(
		"Has Role",
		filters={"role": "Discount Approver", "parenttype": "User"},
		pluck="parent",
	)


def _notify_owner_on_rejection(so_doc, reason):
	"""Send email + in-app notification to the SO owner on rejection."""
	owner = so_doc.owner
	if not owner:
		return

	subject = _("Sales Order {0} – Discount Rejected").format(so_doc.name)
	message = _(
		"Your Sales Order <b>{name}</b> has been <b>rejected</b> by the discount approver.<br><br>"
		"<b>Rejection Reason:</b> {reason}<br><br>"
		"<b>Discounted Items:</b><br>{items}<br><br>"
		"<a href='/app/sales-order/{name}'>Open Sales Order</a>"
	).format(
		name=so_doc.name,
		reason=reason,
		items=(so_doc.custom_approval_reason or "").replace("\n", "<br>"),
	)

	frappe.sendmail(recipients=[owner], subject=subject, message=message, delayed=False)

	try:
		frappe.get_doc({
			"doctype": "Notification Log",
			"subject": subject,
			"email_content": message,
			"for_user": owner,
			"type": "Alert",
			"document_type": "Sales Order",
			"document_name": so_doc.name,
		}).insert(ignore_permissions=True)
	except Exception:
		pass


def _insert_approval_log(sales_order, approval_status, item_details="",
                         reviewed_by=None, approved_by=None,
                         rejection_reason=None):
	"""Insert a Discount Approval Log entry."""
	try:
		frappe.get_doc({
			"doctype": "Discount Approval Log",
			"sales_order": sales_order,
			"approval_status": approval_status,
			"item_details_json": item_details,
			"reviewed_by": reviewed_by,
			"approved_by": approved_by,
			"rejection_reason": rejection_reason or "",
			"timestamp": now_datetime(),
		}).insert(ignore_permissions=True)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Discount Approval Log insert failed")
