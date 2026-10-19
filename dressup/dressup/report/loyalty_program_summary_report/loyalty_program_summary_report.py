# Copyright (c) 2026, Prime Technology of Bangladesh and contributors
# For license information, please see license.txt

"""
Loyalty Program Summary Report
================================
Customer-ভিত্তিক Loyalty Program সামারি রিপোর্ট।

কলাম:
- Customer, Customer Name
- Loyalty Program, Current Tier
- Total Earned Points, Total Redeemed Points, Balance Points
- Points Expiring ≤ N Days
- This Month Spend, 12-Month (Rolling) Spend
- Last Transaction Date
"""

import frappe
from frappe import _
from frappe.utils import add_years, flt, getdate, today, add_days


def execute(filters=None):
	if isinstance(filters, str):
		filters = frappe.parse_json(filters)
	if not filters:
		filters = {}

	validate_filters(filters)
	columns = get_columns()
	data = get_data(filters)
	summary = get_report_summary(data)
	return columns, data, None, None, summary


# ─────────────────────────────────────────────────────────────────────────────
# Validation
# ─────────────────────────────────────────────────────────────────────────────

def validate_filters(filters):
	if not filters.get("company"):
		frappe.throw(_("Company is required"))


# ─────────────────────────────────────────────────────────────────────────────
# Columns
# ─────────────────────────────────────────────────────────────────────────────

def get_columns():
	return [
		{
			"label": _("Customer"),
			"fieldname": "customer",
			"fieldtype": "Link",
			"options": "Customer",
			"width": 150,
		},
		{
			"label": _("Customer Name"),
			"fieldname": "customer_name",
			"fieldtype": "Data",
			"width": 190,
		},
		{
			"label": _("Loyalty Program"),
			"fieldname": "loyalty_program",
			"fieldtype": "Link",
			"options": "Loyalty Program",
			"width": 170,
		},
		{
			"label": _("Current Tier"),
			"fieldname": "current_tier",
			"fieldtype": "Data",
			"width": 120,
		},
		{
			"label": _("Total Earned Pts"),
			"fieldname": "total_earned",
			"fieldtype": "Float",
			"precision": 2,
			"width": 140,
		},
		{
			"label": _("Total Redeemed Pts"),
			"fieldname": "total_redeemed",
			"fieldtype": "Float",
			"precision": 2,
			"width": 150,
		},
		{
			"label": _("Balance Points"),
			"fieldname": "balance_points",
			"fieldtype": "Float",
			"precision": 2,
			"width": 130,
		},
		{
			"label": _("Expiring ≤7 Days"),
			"fieldname": "expiring_soon",
			"fieldtype": "Float",
			"precision": 2,
			"width": 145,
		},
		{
			"label": _("This Month Spend"),
			"fieldname": "month_spend",
			"fieldtype": "Currency",
			"options": "currency",
			"width": 150,
		},
		{
			"label": _("12-Month Spend"),
			"fieldname": "yearly_spend",
			"fieldtype": "Currency",
			"options": "currency",
			"width": 150,
		},
		{
			"label": _("Last Transaction"),
			"fieldname": "last_txn_date",
			"fieldtype": "Date",
			"width": 130,
		},
		{
			"label": _("Currency"),
			"fieldname": "currency",
			"fieldtype": "Currency",
			"hidden": 1,
			"width": 80,
		},
	]


# ─────────────────────────────────────────────────────────────────────────────
# Data
# ─────────────────────────────────────────────────────────────────────────────

def get_data(filters):
	company = filters.get("company")
	loyalty_program_filter = filters.get("loyalty_program")
	tier_filter = filters.get("tier")
	expiry_warning_days = int(filters.get("expiry_warning_days") or 7)

	company_currency = (
		frappe.get_cached_value("Company", company, "default_currency") or "BDT"
	)

	today_date = today()
	start_of_month = frappe.utils.get_first_day(today_date)
	one_year_ago = add_years(today_date, -1)
	expiry_threshold = add_days(today_date, expiry_warning_days)

	# Build customer filter conditions
	cust_conditions = ["c.loyalty_program IS NOT NULL", "c.loyalty_program != ''", "c.disabled = 0"]
	if loyalty_program_filter:
		cust_conditions.append("c.loyalty_program = %(loyalty_program)s")
	if tier_filter:
		cust_conditions.append("c.loyalty_program_tier = %(tier)s")

	cust_where = " AND ".join(cust_conditions)

	# Main query: customers enrolled in a loyalty program
	customers = frappe.db.sql(
		f"""
		SELECT
			c.name AS customer,
			c.customer_name,
			c.loyalty_program,
			c.loyalty_program_tier AS current_tier
		FROM `tabCustomer` c
		WHERE {cust_where}
		ORDER BY c.customer_name ASC
		""",
		{"loyalty_program": loyalty_program_filter, "tier": tier_filter},
		as_dict=True,
	)

	if not customers:
		return []

	customer_names = [c.customer for c in customers]

	# ── Loyalty Point Entries aggregated per customer ──────────────────────
	lpe_data = frappe.db.sql(
		"""
		SELECT
			lpe.customer,
			SUM(CASE WHEN lpe.loyalty_points > 0 THEN lpe.loyalty_points ELSE 0 END) AS total_earned,
			SUM(CASE WHEN lpe.loyalty_points < 0 THEN ABS(lpe.loyalty_points) ELSE 0 END) AS total_redeemed,
			SUM(CASE
				WHEN lpe.expiry_date BETWEEN %(today)s AND %(expiry_threshold)s
					AND lpe.loyalty_points > 0
				THEN lpe.loyalty_points
				ELSE 0
			END) AS expiring_soon
		FROM `tabLoyalty Point Entry` lpe
		WHERE lpe.customer IN %(customer_names)s
			AND lpe.docstatus = 1
		GROUP BY lpe.customer
		""",
		{
			"today": today_date,
			"expiry_threshold": expiry_threshold,
			"customer_names": customer_names,
		},
		as_dict=True,
	)
	lpe_map = {d.customer: d for d in lpe_data}

	# ── Month-to-date spend per customer ──────────────────────────────────
	month_spend_data = frappe.db.sql(
		"""
		SELECT
			si.customer,
			COALESCE(SUM(si.net_total), 0) AS month_spend
		FROM `tabSales Invoice` si
		WHERE si.customer IN %(customer_names)s
			AND si.company = %(company)s
			AND si.docstatus = 1
			AND si.is_return = 0
			AND si.posting_date BETWEEN %(start_of_month)s AND %(today)s
		GROUP BY si.customer
		""",
		{
			"customer_names": customer_names,
			"company": company,
			"start_of_month": start_of_month,
			"today": today_date,
		},
		as_dict=True,
	)
	month_spend_map = {d.customer: flt(d.month_spend) for d in month_spend_data}

	# ── 12-month rolling spend per customer ──────────────────────────────
	yearly_spend_data = frappe.db.sql(
		"""
		SELECT
			si.customer,
			COALESCE(SUM(si.net_total), 0) AS yearly_spend
		FROM `tabSales Invoice` si
		WHERE si.customer IN %(customer_names)s
			AND si.company = %(company)s
			AND si.docstatus = 1
			AND si.is_return = 0
			AND si.posting_date BETWEEN %(one_year_ago)s AND %(today)s
		GROUP BY si.customer
		""",
		{
			"customer_names": customer_names,
			"company": company,
			"one_year_ago": one_year_ago,
			"today": today_date,
		},
		as_dict=True,
	)
	yearly_spend_map = {d.customer: flt(d.yearly_spend) for d in yearly_spend_data}

	# ── Last transaction date per customer ────────────────────────────────
	last_txn_data = frappe.db.sql(
		"""
		SELECT
			si.customer,
			MAX(si.posting_date) AS last_txn_date
		FROM `tabSales Invoice` si
		WHERE si.customer IN %(customer_names)s
			AND si.company = %(company)s
			AND si.docstatus = 1
			AND si.is_return = 0
		GROUP BY si.customer
		""",
		{"customer_names": customer_names, "company": company},
		as_dict=True,
	)
	last_txn_map = {d.customer: d.last_txn_date for d in last_txn_data}

	# ── Assemble final rows ───────────────────────────────────────────────
	data = []
	for cust in customers:
		lpe = lpe_map.get(cust.customer, {})
		earned = flt(lpe.get("total_earned", 0))
		redeemed = flt(lpe.get("total_redeemed", 0))
		balance = earned - redeemed
		expiring = flt(lpe.get("expiring_soon", 0))

		row = {
			"customer": cust.customer,
			"customer_name": cust.customer_name,
			"loyalty_program": cust.loyalty_program,
			"current_tier": cust.current_tier or "",
			"total_earned": earned,
			"total_redeemed": redeemed,
			"balance_points": balance,
			"expiring_soon": expiring,
			"month_spend": month_spend_map.get(cust.customer, 0.0),
			"yearly_spend": yearly_spend_map.get(cust.customer, 0.0),
			"last_txn_date": last_txn_map.get(cust.customer),
			"currency": company_currency,
		}
		data.append(row)

	return data


# ─────────────────────────────────────────────────────────────────────────────
# Report Summary
# ─────────────────────────────────────────────────────────────────────────────

def get_report_summary(data):
	if not data:
		return []

	total_customers = len(data)
	total_balance = sum(flt(r.get("balance_points", 0)) for r in data)
	total_expiring = sum(flt(r.get("expiring_soon", 0)) for r in data)
	total_yearly = sum(flt(r.get("yearly_spend", 0)) for r in data)
	currency = data[0].get("currency", "BDT") if data else "BDT"

	return [
		{
			"value": total_customers,
			"label": _("Enrolled Customers"),
			"datatype": "Int",
			"indicator": "Blue",
		},
		{
			"value": total_balance,
			"label": _("Total Balance Points"),
			"datatype": "Float",
			"indicator": "Green",
		},
		{
			"value": total_expiring,
			"label": _("Points Expiring Soon"),
			"datatype": "Float",
			"indicator": "Orange" if total_expiring > 0 else "Green",
		},
		{
			"value": total_yearly,
			"label": _("Total 12-Month Spend"),
			"datatype": "Currency",
			"currency": currency,
			"indicator": "Blue",
		},
	]

