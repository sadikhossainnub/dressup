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
	return columns, data


# ---------------------------------------------------------------------------
# Columns
# ---------------------------------------------------------------------------

def get_columns():
	return [
		# ── Sales Order ───────────────────────────────────────────────────────
		{
			"label":     _("Sales Order"),
			"fieldname": "sales_order",
			"fieldtype": "Link",
			"options":   "Sales Order",
			"width":     160,
		},
		{
			"label":     _("SO Date"),
			"fieldname": "so_date",
			"fieldtype": "Date",
			"width":     100,
		},
		{
			"label":     _("SO Delivery Date"),
			"fieldname": "so_delivery_date",
			"fieldtype": "Date",
			"width":     120,
		},
		{
			"label":     _("SO Status"),
			"fieldname": "so_status",
			"fieldtype": "Data",
			"width":     160,
		},
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
			"width":     100,
		},

		# ── Customer ──────────────────────────────────────────────────────────
		{
			"label":     _("Customer"),
			"fieldname": "customer",
			"fieldtype": "Link",
			"options":   "Customer",
			"width":     150,
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
			"width":     110,
		},

		# ── Item ─────────────────────────────────────────────────────────────
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
			"label":     _("UOM"),
			"fieldname": "uom",
			"fieldtype": "Data",
			"width":     70,
		},

		# ── Qty Columns ───────────────────────────────────────────────────────
		{
			"label":     _("SO Qty"),
			"fieldname": "so_qty",
			"fieldtype": "Float",
			"width":     90,
		},
		{
			"label":     _("Delivered Qty"),
			"fieldname": "dn_qty",
			"fieldtype": "Float",
			"width":     110,
		},
		{
			"label":     _("Pending Qty"),
			"fieldname": "pending_qty",
			"fieldtype": "Float",
			"width":     110,
		},

		# ── Amount ────────────────────────────────────────────────────────────
		{
			"label":     _("SO Rate"),
			"fieldname": "so_rate",
			"fieldtype": "Currency",
			"options":   "currency",
			"width":     100,
		},
		{
			"label":     _("SO Amount"),
			"fieldname": "so_amount",
			"fieldtype": "Currency",
			"options":   "currency",
			"width":     120,
		},
		{
			"label":     _("SO Grand Total"),
			"fieldname": "so_grand_total",
			"fieldtype": "Currency",
			"options":   "currency",
			"width":     130,
		},
		{
			"label":     _("Currency"),
			"fieldname": "currency",
			"fieldtype": "Data",
			"width":     80,
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
			"fieldname": "dn_date",
			"fieldtype": "Date",
			"width":     100,
		},
		{
			"label":     _("DN Status"),
			"fieldname": "dn_status",
			"fieldtype": "Data",
			"width":     120,
		},
		{
			"label":     _("DN Grand Total"),
			"fieldname": "dn_grand_total",
			"fieldtype": "Currency",
			"options":   "currency",
			"width":     130,
		},

		# ── Misc ──────────────────────────────────────────────────────────────
		{
			"label":     _("Sales Person"),
			"fieldname": "sales_person",
			"fieldtype": "Data",
			"width":     140,
		},
		{
			"label":     _("PO No"),
			"fieldname": "po_no",
			"fieldtype": "Data",
			"width":     120,
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
	conditions, values = build_so_conditions(filters)

	# ── Step 1: fetch SO + SO Items ─────────────────────────────────────────
	rows = frappe.db.sql(
		f"""
		SELECT
			so.name                    AS sales_order,
			so.transaction_date        AS so_date,
			so.delivery_date           AS so_delivery_date,
			so.status                  AS so_status,
			so.per_delivered           AS per_delivered,
			so.customer                AS customer,
			so.customer_name           AS customer_name,
			so.customer_group          AS customer_group,
			so.territory               AS territory,
			so.grand_total             AS so_grand_total,
			so.currency                AS currency,
			so.po_no                   AS po_no,
			so.company                 AS company,
			soi.name                   AS soi_name,
			soi.item_code              AS item_code,
			soi.item_name              AS item_name,
			soi.uom                    AS uom,
			soi.qty                    AS so_qty,
			soi.delivered_qty          AS delivered_qty,
			soi.rate                   AS so_rate,
			soi.amount                 AS so_amount
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

	if not rows:
		return []

	# ── Step 2: attach sales persons ────────────────────────────────────────
	rows = attach_sales_persons(rows)

	# ── Step 3: attach delivery notes ───────────────────────────────────────
	rows = attach_delivery_notes(rows, filters)

	# ── Step 4: compute delivery status and pending qty ─────────────────────
	for row in rows:
		row["delivery_status"] = compute_delivery_status(flt(row.get("per_delivered")))
		row["pending_qty"]     = flt(row.get("so_qty")) - flt(row.get("dn_qty"))

	# ── Step 5: apply post-fetch filters ────────────────────────────────────
	rows = apply_post_filters(rows, filters)

	return rows


# ---------------------------------------------------------------------------
# Condition Builder
# ---------------------------------------------------------------------------

def build_so_conditions(filters):
	parts  = []
	values = {}

	if filters.get("company"):
		parts.append("AND so.company = %(company)s")
		values["company"] = filters["company"]

	date_based_on = filters.get("date_based_on") or "Sales Order Date"

	if date_based_on == "Sales Order Date":
		if filters.get("from_date"):
			parts.append("AND so.transaction_date >= %(from_date)s")
			values["from_date"] = filters["from_date"]
		if filters.get("to_date"):
			parts.append("AND so.transaction_date <= %(to_date)s")
			values["to_date"] = filters["to_date"]
	# "Delivery Note Date" filtering is done post-fetch (in apply_post_filters)

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

	if filters.get("so_status"):
		parts.append("AND so.status = %(so_status)s")
		values["so_status"] = filters["so_status"]

	if filters.get("item_code"):
		parts.append("AND soi.item_code = %(item_code)s")
		values["item_code"] = filters["item_code"]

	return " ".join(parts), values


# ---------------------------------------------------------------------------
# Post-fetch Filters
# ---------------------------------------------------------------------------

def apply_post_filters(rows, filters):
	date_based_on = filters.get("date_based_on") or "Sales Order Date"

	filtered = []
	for row in rows:
		# Date filter on DN date
		if date_based_on == "Delivery Note Date":
			from_date = filters.get("from_date")
			to_date   = filters.get("to_date")
			dn_date   = row.get("dn_date")
			if from_date and dn_date and str(dn_date) < str(from_date):
				continue
			if to_date and dn_date and str(dn_date) > str(to_date):
				continue

		# Delivery status filter
		if filters.get("delivery_status"):
			if row.get("delivery_status") != filters["delivery_status"]:
				continue

		# DN status filter
		if filters.get("dn_status"):
			if row.get("dn_status") != filters["dn_status"]:
				continue

		filtered.append(row)

	return filtered


# ---------------------------------------------------------------------------
# Helper: Delivery Notes
# ---------------------------------------------------------------------------

def attach_delivery_notes(rows, filters=None):
	"""
	Bulk-fetch the FIRST Delivery Note per SO Item and attach DN details.
	If a SO Item has multiple DNs, names are comma-separated and qty/totals summed.
	"""
	if not rows:
		return rows

	soi_names   = list({r["soi_name"] for r in rows if r.get("soi_name")})
	dn_map      = {}   # soi_name -> aggregated dict
	chunk_size  = 200

	for i in range(0, len(soi_names), chunk_size):
		chunk        = soi_names[i : i + chunk_size]
		placeholders = ", ".join(["%s"] * len(chunk))

		dn_rows = frappe.db.sql(
			f"""
			SELECT
				dni.so_detail      AS soi_name,
				dni.parent         AS delivery_note,
				dni.qty            AS dn_item_qty,
				dn.posting_date    AS dn_date,
				dn.status          AS dn_status,
				dn.grand_total     AS dn_grand_total
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
			key = dn["soi_name"]
			if key not in dn_map:
				dn_map[key] = {
					"delivery_note":  dn["delivery_note"],
					"dn_date":        dn["dn_date"],
					"dn_status":      dn["dn_status"],
					"dn_qty":         flt(dn["dn_item_qty"]),
					"dn_grand_total": flt(dn["dn_grand_total"]),
				}
			else:
				existing = dn_map[key]
				# Append DN name (comma-separated)
				existing["delivery_note"] = (
					(existing["delivery_note"] or "") + ", " + (dn["delivery_note"] or "")
				).strip(", ")
				# Keep earliest date, accumulate qty and total
				existing["dn_qty"]         += flt(dn["dn_item_qty"])
				existing["dn_grand_total"] += flt(dn["dn_grand_total"])

	for row in rows:
		info = dn_map.get(row.get("soi_name")) or {}
		row["delivery_note"]  = info.get("delivery_note")  or ""
		row["dn_date"]        = info.get("dn_date")        or ""
		row["dn_status"]      = info.get("dn_status")      or ""
		row["dn_qty"]         = flt(info.get("dn_qty"))
		row["dn_grand_total"] = flt(info.get("dn_grand_total"))

	return rows


# ---------------------------------------------------------------------------
# Helper: Sales Persons
# ---------------------------------------------------------------------------

def attach_sales_persons(rows):
	"""Fetch all sales team entries for the SOs in the result set."""
	if not rows:
		return rows

	so_names   = list({r["sales_order"] for r in rows})
	chunk_size = 200
	sp_map     = {}

	for i in range(0, len(so_names), chunk_size):
		chunk        = so_names[i : i + chunk_size]
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


# ---------------------------------------------------------------------------
# Helper: Delivery Status Label
# ---------------------------------------------------------------------------

def compute_delivery_status(per_delivered):
	pct = flt(per_delivered)
	if pct <= 0:
		return "Not Delivered"
	elif pct < 100:
		return "Partially Delivered"
	else:
		return "Fully Delivered"
