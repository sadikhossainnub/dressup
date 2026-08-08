# Copyright (c) 2026, Prime Technology of Bangladesh and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt


def execute(filters=None):
	if not filters:
		filters = {}
	columns = get_columns()
	data    = get_data(filters)

	if data:
		data.append(get_total_row(data))

	return columns, data


# ---------------------------------------------------------------------------
# Total Row
# ---------------------------------------------------------------------------

def get_total_row(data):
	"""Return a bold summary row summing all numeric/currency columns."""
	# Numeric fields to sum
	sum_fields = [
		"qty", "amount", "delivered_qty", "billed_amt",
		"total_qty", "net_total", "total_taxes_and_charges",
		"grand_total", "advance_paid", "outstanding_amount",
		"si_grand_total", "si_outstanding_amount",
	]

	totals = {f: 0.0 for f in sum_fields}
	for row in data:
		for f in sum_fields:
			totals[f] = flt(totals[f]) + flt(row.get(f) or 0)

	total_row = {
		"sales_order":    _("Total"),
		"bold":           1,
	}
	total_row.update(totals)
	return total_row


# ---------------------------------------------------------------------------
# Columns
# ---------------------------------------------------------------------------

def get_columns():
	return [
		# ── Identity ─────────────────────────────────────────────────────────
		{
			"label":     _("Sales Order"),
			"fieldname": "sales_order",
			"fieldtype": "Link",
			"options":   "Sales Order",
			"width":     160,
		},
		{
			"label":     _("Date"),
			"fieldname": "transaction_date",
			"fieldtype": "Date",
			"width":     100,
		},
		{
			"label":     _("Delivery Date"),
			"fieldname": "delivery_date",
			"fieldtype": "Date",
			"width":     110,
		},
		{
			"label":     _("Status"),
			"fieldname": "status",
			"fieldtype": "Data",
			"width":     160,
		},

		# ── Delivery Status ──────────────────────────────────────────────────
		{
			"label":     _("Delivery Status"),
			"fieldname": "delivery_status",
			"fieldtype": "Data",
			"width":     150,
		},
		{
			"label":     _("% Delivered"),
			"fieldname": "per_delivered",
			"fieldtype": "Percent",
			"width":     110,
		},

		# ── Delivery Note ─────────────────────────────────────────────────────
		{
			"label":     _("Delivery Note"),
			"fieldname": "delivery_note",
			"fieldtype": "Link",
			"options":   "Delivery Note",
			"width":     160,
		},
		{
			"label":     _("DN Date"),
			"fieldname": "dn_posting_date",
			"fieldtype": "Date",
			"width":     100,
		},
		{
			"label":     _("DN Status"),
			"fieldname": "dn_status",
			"fieldtype": "Data",
			"width":     130,
		},

		# ── Sales Invoice ─────────────────────────────────────────────────
		{
			"label":     _("Sales Invoice"),
			"fieldname": "sales_invoice",
			"fieldtype": "Link",
			"options":   "Sales Invoice",
			"width":     165,
		},
		{
			"label":     _("SI Date"),
			"fieldname": "si_posting_date",
			"fieldtype": "Date",
			"width":     100,
		},
		{
			"label":     _("SI Status"),
			"fieldname": "si_status",
			"fieldtype": "Data",
			"width":     130,
		},
		{
			"label":     _("SI Grand Total"),
			"fieldname": "si_grand_total",
			"fieldtype": "Currency",
			"options":   "currency",
			"width":     130,
		},
		{
			"label":     _("SI Outstanding"),
			"fieldname": "si_outstanding_amount",
			"fieldtype": "Currency",
			"options":   "currency",
			"width":     140,
		},

		# ── Created By ───────────────────────────────────────────────────────
		{
			"label":     _("Created By"),
			"fieldname": "created_by",
			"fieldtype": "Link",
			"options":   "User",
			"width":     180,
		},
		{
			"label":     _("Created On"),
			"fieldname": "creation",
			"fieldtype": "Datetime",
			"width":     160,
		},

		# ── Customer ─────────────────────────────────────────────────────────
		{
			"label":     _("Customer"),
			"fieldname": "customer",
			"fieldtype": "Link",
			"options":   "Customer",
			"width":     160,
		},
		{
			"label":     _("Customer Name"),
			"fieldname": "customer_name",
			"fieldtype": "Data",
			"width":     160,
		},
		{
			"label":     _("Customer Group"),
			"fieldname": "customer_group",
			"fieldtype": "Link",
			"options":   "Customer Group",
			"width":     130,
		},
		{
			"label":     _("Territory"),
			"fieldname": "territory",
			"fieldtype": "Link",
			"options":   "Territory",
			"width":     120,
		},
		{
			"label":     _("Contact"),
			"fieldname": "contact_display",
			"fieldtype": "Data",
			"width":     130,
		},

		# ── Sales Team ───────────────────────────────────────────────────────
		{
			"label":     _("Sales Person"),
			"fieldname": "sales_person",
			"fieldtype": "Data",
			"width":     140,
		},

		# ── Items ────────────────────────────────────────────────────────────
		{
			"label":     _("Item Code"),
			"fieldname": "item_code",
			"fieldtype": "Link",
			"options":   "Item",
			"width":     140,
		},
		{
			"label":     _("Item Name"),
			"fieldname": "item_name",
			"fieldtype": "Data",
			"width":     160,
		},
		{
			"label":     _("Qty"),
			"fieldname": "qty",
			"fieldtype": "Float",
			"width":     80,
		},
		{
			"label":     _("UOM"),
			"fieldname": "uom",
			"fieldtype": "Data",
			"width":     70,
		},
		{
			"label":     _("Rate"),
			"fieldname": "rate",
			"fieldtype": "Currency",
			"options":   "currency",
			"width":     100,
		},
		{
			"label":     _("Discount %"),
			"fieldname": "discount_percentage",
			"fieldtype": "Percent",
			"width":     100,
		},
		{
			"label":     _("Amount"),
			"fieldname": "amount",
			"fieldtype": "Currency",
			"options":   "currency",
			"width":     120,
		},
		{
			"label":     _("Delivered Qty"),
			"fieldname": "delivered_qty",
			"fieldtype": "Float",
			"width":     110,
		},
		{
			"label":     _("Billed Qty"),
			"fieldname": "billed_amt",
			"fieldtype": "Currency",
			"options":   "currency",
			"width":     110,
		},

		# ── Totals ───────────────────────────────────────────────────────────
		{
			"label":     _("Total Qty"),
			"fieldname": "total_qty",
			"fieldtype": "Float",
			"width":     90,
		},
		{
			"label":     _("Net Total"),
			"fieldname": "net_total",
			"fieldtype": "Currency",
			"options":   "currency",
			"width":     120,
		},
		{
			"label":     _("Tax Amount"),
			"fieldname": "total_taxes_and_charges",
			"fieldtype": "Currency",
			"options":   "currency",
			"width":     110,
		},
		{
			"label":     _("Grand Total"),
			"fieldname": "grand_total",
			"fieldtype": "Currency",
			"options":   "currency",
			"width":     130,
		},
		{
			"label":     _("Advance Paid"),
			"fieldname": "advance_paid",
			"fieldtype": "Currency",
			"options":   "currency",
			"width":     110,
		},
		{
			"label":     _("Outstanding Amount"),
			"fieldname": "outstanding_amount",
			"fieldtype": "Currency",
			"options":   "currency",
			"width":     140,
		},
		{
			"label":     _("Currency"),
			"fieldname": "currency",
			"fieldtype": "Data",
			"width":     80,
		},

		# ── Approval (custom fields) ─────────────────────────────────────────
		{
			"label":     _("Has Extra Discount"),
			"fieldname": "has_extra_discount",
			"fieldtype": "Check",
			"width":     130,
		},
		{
			"label":     _("Approval Status"),
			"fieldname": "approval_status",
			"fieldtype": "Data",
			"width":     130,
		},
		{
			"label":     _("Reviewed By"),
			"fieldname": "reviewed_by",
			"fieldtype": "Link",
			"options":   "User",
			"width":     160,
		},
		{
			"label":     _("Approved By"),
			"fieldname": "approved_by",
			"fieldtype": "Link",
			"options":   "User",
			"width":     160,
		},
		{
			"label":     _("Approved On"),
			"fieldname": "approved_on",
			"fieldtype": "Date",
			"width":     110,
		},
		{
			"label":     _("Rejection Reason"),
			"fieldname": "rejection_reason",
			"fieldtype": "Data",
			"width":     180,
		},

		# ── Misc ─────────────────────────────────────────────────────────────
		{
			"label":     _("PO No"),
			"fieldname": "po_no",
			"fieldtype": "Data",
			"width":     120,
		},
		{
			"label":     _("PO Date"),
			"fieldname": "po_date",
			"fieldtype": "Date",
			"width":     100,
		},
		{
			"label":     _("Source"),
			"fieldname": "source",
			"fieldtype": "Data",
			"width":     100,
		},
		{
			"label":     _("Company"),
			"fieldname": "company",
			"fieldtype": "Link",
			"options":   "Company",
			"width":     130,
		},
	]


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------

def get_data(filters):
	conditions, values = build_conditions(filters)

	# Main query — one row per SO Item so Grand Total / Outstanding are repeated
	rows = frappe.db.sql(
		f"""
		SELECT
			so.name                        AS sales_order,
			so.transaction_date            AS transaction_date,
			so.delivery_date               AS delivery_date,
			so.status                      AS status,
			so.per_delivered               AS per_delivered,
			so.owner                       AS created_by,
			so.creation                    AS creation,
			so.customer                    AS customer,
			so.customer_name               AS customer_name,
			so.customer_group              AS customer_group,
			so.territory                   AS territory,
			so.contact_display             AS contact_display,
			so.total_qty                   AS total_qty,
			so.net_total                   AS net_total,
			so.total_taxes_and_charges     AS total_taxes_and_charges,
			so.grand_total                 AS grand_total,
			so.advance_paid                AS advance_paid,
			(so.grand_total - so.advance_paid)
			                               AS outstanding_amount,
			so.currency                    AS currency,
			so.po_no                       AS po_no,
			so.po_date                     AS po_date,
			so.source                      AS source,
			so.company                     AS company,
			-- Custom approval fields
			so.custom_has_extra_discount   AS has_extra_discount,
			so.custom_approval_status      AS approval_status,
			so.custom_reviewed_by          AS reviewed_by,
			so.custom_approved_by          AS approved_by,
			so.custom_approved_on          AS approved_on,
			so.custom_rejection_reason     AS rejection_reason,
			-- Item-level columns
			soi.name                       AS soi_name,
			soi.item_code                  AS item_code,
			soi.item_name                  AS item_name,
			soi.qty                        AS qty,
			soi.uom                        AS uom,
			soi.rate                       AS rate,
			soi.discount_percentage        AS discount_percentage,
			soi.amount                     AS amount,
			soi.delivered_qty              AS delivered_qty,
			soi.billed_amt                 AS billed_amt
		FROM
			`tabSales Order` so
		INNER JOIN
			`tabSales Order Item` soi ON soi.parent = so.name
		WHERE
			so.docstatus < 2
			{conditions}
		ORDER BY
			so.transaction_date DESC, so.name ASC, soi.idx ASC
		""",
		values,
		as_dict=True,
	)

	# Fetch sales persons in one shot and attach
	rows = attach_sales_persons(rows)

	# Fetch linked Delivery Notes per SO item and attach
	rows = attach_delivery_notes(rows)

	# Fetch linked Sales Invoices per SO item and attach
	rows = attach_sales_invoices(rows)

	# Compute delivery status label from per_delivered
	for row in rows:
		row["delivery_status"] = compute_delivery_status(row.get("per_delivered") or 0)

	return rows


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def build_conditions(filters):
	parts  = []
	values = {}

	if filters.get("company"):
		parts.append("AND so.company = %(company)s")
		values["company"] = filters["company"]

	if filters.get("from_date"):
		parts.append("AND so.transaction_date >= %(from_date)s")
		values["from_date"] = filters["from_date"]

	if filters.get("to_date"):
		parts.append("AND so.transaction_date <= %(to_date)s")
		values["to_date"] = filters["to_date"]

	if filters.get("sales_order"):
		parts.append("AND so.name = %(sales_order)s")
		values["sales_order"] = filters["sales_order"]

	if filters.get("customer"):
		parts.append("AND so.customer = %(customer)s")
		values["customer"] = filters["customer"]

	if filters.get("customer_group"):
		parts.append("AND so.customer_group = %(customer_group)s")
		values["customer_group"] = filters["customer_group"]

	if filters.get("territory"):
		parts.append("AND so.territory = %(territory)s")
		values["territory"] = filters["territory"]

	if filters.get("status"):
		parts.append("AND so.status = %(status)s")
		values["status"] = filters["status"]

	if filters.get("created_by"):
		parts.append("AND so.owner = %(created_by)s")
		values["created_by"] = filters["created_by"]

	if filters.get("approval_status"):
		parts.append("AND so.custom_approval_status = %(approval_status)s")
		values["approval_status"] = filters["approval_status"]

	if filters.get("item_code"):
		parts.append("AND soi.item_code = %(item_code)s")
		values["item_code"] = filters["item_code"]

	if filters.get("sales_person"):
		parts.append(
			"""AND so.name IN (
				SELECT parent FROM `tabSales Team`
				WHERE sales_person = %(sales_person)s
				  AND parenttype = 'Sales Order'
			)"""
		)
		values["sales_person"] = filters["sales_person"]

	return " ".join(parts), values


def compute_delivery_status(per_delivered):
	"""Return a human-readable delivery status from the per_delivered percentage."""
	pct = flt(per_delivered)
	if pct <= 0:
		return "Not Delivered"
	elif pct < 100:
		return "Partially Delivered"
	else:
		return "Fully Delivered"


def attach_delivery_notes(rows):
	"""Bulk-fetch Delivery Notes linked to each Sales Order Item and attach to rows."""
	if not rows:
		return rows

	soi_names = list({r["soi_name"] for r in rows if r.get("soi_name")})
	dn_map = {}  # soi_name -> {delivery_note, dn_posting_date, dn_status}

	chunk_size = 200
	for i in range(0, len(soi_names), chunk_size):
		chunk = soi_names[i : i + chunk_size]
		placeholders = ", ".join(["%s"] * len(chunk))
		dn_rows = frappe.db.sql(
			f"""
			SELECT
				dni.so_detail          AS soi_name,
				dni.parent             AS delivery_note,
				dn.posting_date        AS dn_posting_date,
				dn.status              AS dn_status
			FROM
				`tabDelivery Note Item` dni
			INNER JOIN
				`tabDelivery Note` dn ON dn.name = dni.parent
			WHERE
				dni.so_detail IN ({placeholders})
				AND dn.docstatus < 2
			ORDER BY
				dn.posting_date ASC
			""",
			tuple(chunk),
			as_dict=True,
		)
		for dn in dn_rows:
			# Keep the first (earliest) DN per SOI; if multiple, comma-separate names
			key = dn["soi_name"]
			if key not in dn_map:
				dn_map[key] = dn
			else:
				# Append extra DN names
				existing = dn_map[key]
				existing["delivery_note"] = (
					(existing["delivery_note"] or "") + ", " + (dn["delivery_note"] or "")
				).strip(", ")

	for row in rows:
		dn_info = dn_map.get(row.get("soi_name")) or {}
		row["delivery_note"]    = dn_info.get("delivery_note") or ""
		row["dn_posting_date"]  = dn_info.get("dn_posting_date") or ""
		row["dn_status"]        = dn_info.get("dn_status") or ""

	return rows


def attach_sales_invoices(rows):
	"""Bulk-fetch Sales Invoices linked to each Sales Order Item and attach to rows."""
	if not rows:
		return rows

	soi_names = list({r["soi_name"] for r in rows if r.get("soi_name")})
	si_map = {}  # soi_name -> {sales_invoice, si_posting_date, si_status, si_grand_total, si_outstanding_amount}

	chunk_size = 200
	for i in range(0, len(soi_names), chunk_size):
		chunk = soi_names[i : i + chunk_size]
		placeholders = ", ".join(["%s"] * len(chunk))
		si_rows = frappe.db.sql(
			f"""
			SELECT
				sii.sales_order_item   AS soi_name,
				sii.parent             AS sales_invoice,
				si.posting_date        AS si_posting_date,
				si.status              AS si_status,
				si.grand_total         AS si_grand_total,
				si.outstanding_amount  AS si_outstanding_amount
			FROM
				`tabSales Invoice Item` sii
			INNER JOIN
				`tabSales Invoice` si ON si.name = sii.parent
			WHERE
				sii.sales_order_item IN ({placeholders})
				AND si.docstatus < 2
			ORDER BY
				si.posting_date ASC
			""",
			tuple(chunk),
			as_dict=True,
		)
		for si in si_rows:
			key = si["soi_name"]
			if key not in si_map:
				si_map[key] = si
			else:
				# Multiple invoices: append names, accumulate totals
				existing = si_map[key]
				existing["sales_invoice"] = (
					(existing["sales_invoice"] or "") + ", " + (si["sales_invoice"] or "")
				).strip(", ")
				existing["si_grand_total"]        = flt(existing.get("si_grand_total")) + flt(si.get("si_grand_total"))
				existing["si_outstanding_amount"] = flt(existing.get("si_outstanding_amount")) + flt(si.get("si_outstanding_amount"))

	for row in rows:
		si_info = si_map.get(row.get("soi_name")) or {}
		row["sales_invoice"]        = si_info.get("sales_invoice") or ""
		row["si_posting_date"]      = si_info.get("si_posting_date") or ""
		row["si_status"]            = si_info.get("si_status") or ""
		row["si_grand_total"]       = flt(si_info.get("si_grand_total"))
		row["si_outstanding_amount"]= flt(si_info.get("si_outstanding_amount"))

	return rows


def attach_sales_persons(rows):
	"""Fetch all sales team entries for the SOs in the result set and attach as a comma-separated string."""
	if not rows:
		return rows

	so_names = list({r["sales_order"] for r in rows})

	# chunk to avoid too-large IN clause
	chunk_size = 200
	sp_map = {}
	for i in range(0, len(so_names), chunk_size):
		chunk = so_names[i : i + chunk_size]
		placeholders = ", ".join(["%s"] * len(chunk))
		sales_team = frappe.db.sql(
			f"""
			SELECT parent, GROUP_CONCAT(sales_person ORDER BY idx SEPARATOR ', ') AS sales_persons
			FROM `tabSales Team`
			WHERE parenttype = 'Sales Order'
			  AND parent IN ({placeholders})
			GROUP BY parent
			""",
			tuple(chunk),
			as_dict=True,
		)
		for st in sales_team:
			sp_map[st["parent"]] = st["sales_persons"]

	for row in rows:
		row["sales_person"] = sp_map.get(row["sales_order"], "")

	return rows
