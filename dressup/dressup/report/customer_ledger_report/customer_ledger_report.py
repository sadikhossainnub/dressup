# Copyright (c) 2026, Prime Technology of Bangladesh and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, cstr


def execute(filters=None):
	if not filters:
		filters = {}

	validate_filters(filters)

	columns = get_columns(filters)
	opening_balance = get_opening_balance(filters)
	gl_entries = get_gl_entries(filters)

	data = []

	# Add Opening Balance Row
	running_balance = flt(opening_balance)
	data.append({
		"posting_date": filters.get("from_date"),
		"remarks": _("Opening Balance"),
		"debit": 0.0,
		"credit": 0.0,
		"balance": running_balance,
	})

	total_debit = 0.0
	total_credit = 0.0

	# Process GL Entries
	for entry in gl_entries:
		debit = flt(entry.get("debit"))
		credit = flt(entry.get("credit"))
		running_balance += (debit - credit)
		total_debit += debit
		total_credit += credit

		row = {
			"posting_date": entry.get("posting_date"),
			"account": entry.get("account"),
			"voucher_type": entry.get("voucher_type"),
			"voucher_no": entry.get("voucher_no"),
			"customer": entry.get("party"),
			"customer_name": entry.get("customer_name"),
			"against": entry.get("against"),
			"debit": debit,
			"credit": credit,
			"balance": running_balance,
			"remarks": entry.get("remarks"),
		}
		data.append(row)

	closing_balance = running_balance

	report_summary = get_report_summary(
		opening_balance, total_debit, total_credit, closing_balance, filters
	)

	return columns, data, None, None, report_summary


def validate_filters(filters):
	if not filters.get("company"):
		frappe.throw(_("Company is required"))
	if not filters.get("from_date"):
		frappe.throw(_("From Date is required"))
	if not filters.get("to_date"):
		frappe.throw(_("To Date is required"))
	if filters.get("from_date") > filters.get("to_date"):
		frappe.throw(_("From Date cannot be greater than To Date"))


def get_columns(filters):
	company_currency = frappe.get_cached_value("Company", filters.get("company"), "default_currency") or "BDT"

	return [
		{
			"label": _("Posting Date"),
			"fieldname": "posting_date",
			"fieldtype": "Date",
			"width": 105,
		},
		{
			"label": _("Customer"),
			"fieldname": "customer",
			"fieldtype": "Link",
			"options": "Customer",
			"width": 130,
		},
		{
			"label": _("Customer Name"),
			"fieldname": "customer_name",
			"fieldtype": "Data",
			"width": 160,
		},
		{
			"label": _("Voucher Type"),
			"fieldname": "voucher_type",
			"fieldtype": "Data",
			"width": 130,
		},
		{
			"label": _("Voucher No"),
			"fieldname": "voucher_no",
			"fieldtype": "Dynamic Link",
			"options": "voucher_type",
			"width": 160,
		},
		{
			"label": _("Account"),
			"fieldname": "account",
			"fieldtype": "Link",
			"options": "Account",
			"width": 140,
		},
		{
			"label": _("Against Account"),
			"fieldname": "against",
			"fieldtype": "Data",
			"width": 180,
		},
		{
			"label": _("Debit"),
			"fieldname": "debit",
			"fieldtype": "Currency",
			"options": "company_currency",
			"width": 120,
		},
		{
			"label": _("Credit"),
			"fieldname": "credit",
			"fieldtype": "Currency",
			"options": "company_currency",
			"width": 120,
		},
		{
			"label": _("Balance"),
			"fieldname": "balance",
			"fieldtype": "Currency",
			"options": "company_currency",
			"width": 130,
		},
		{
			"label": _("Remarks"),
			"fieldname": "remarks",
			"fieldtype": "Small Text",
			"width": 200,
		},
	]


def get_conditions(filters):
	conditions = ["gle.company = %(company)s", "gle.party_type = 'Customer'"]

	if not filters.get("show_cancelled"):
		conditions.append("gle.is_cancelled = 0")

	if filters.get("customer"):
		conditions.append("gle.party = %(customer)s")

	if filters.get("account"):
		conditions.append("gle.account = %(account)s")

	if filters.get("customer_group"):
		cust_list = frappe.get_all("Customer", filters={"customer_group": filters.get("customer_group")}, pluck="name")
		if cust_list:
			filters["customer_list"] = cust_list
			conditions.append("gle.party IN %(customer_list)s")
		else:
			conditions.append("1=0")

	return " AND ".join(conditions)


def get_opening_balance(filters):
	conditions = get_conditions(filters)

	query = f"""
		SELECT SUM(gle.debit) - SUM(gle.credit) AS opening_balance
		FROM `tabGL Entry` gle
		WHERE {conditions}
			AND gle.posting_date < %(from_date)s
	"""

	res = frappe.db.sql(query, filters, as_dict=True)
	return flt(res[0].opening_balance) if res and res[0].opening_balance else 0.0


def get_gl_entries(filters):
	conditions = get_conditions(filters)

	query = f"""
		SELECT
			gle.posting_date,
			gle.account,
			gle.voucher_type,
			gle.voucher_no,
			gle.party,
			cust.customer_name,
			gle.against,
			gle.debit,
			gle.credit,
			gle.remarks
		FROM `tabGL Entry` gle
		LEFT JOIN `tabCustomer` cust ON cust.name = gle.party
		WHERE {conditions}
			AND gle.posting_date BETWEEN %(from_date)s AND %(to_date)s
		ORDER BY gle.posting_date ASC, gle.creation ASC
	"""

	return frappe.db.sql(query, filters, as_dict=True)


def get_report_summary(opening_balance, total_debit, total_credit, closing_balance, filters):
	company_currency = frappe.get_cached_value("Company", filters.get("company"), "default_currency") or "BDT"

	return [
		{
			"value": opening_balance,
			"label": _("Opening Balance"),
			"datatype": "Currency",
			"currency": company_currency,
		},
		{
			"value": total_debit,
			"label": _("Total Debit (Invoices)"),
			"datatype": "Currency",
			"currency": company_currency,
			"indicator": "Blue",
		},
		{
			"value": total_credit,
			"label": _("Total Credit (Payments)"),
			"datatype": "Currency",
			"currency": company_currency,
			"indicator": "Green",
		},
		{
			"value": closing_balance,
			"label": _("Closing Balance"),
			"datatype": "Currency",
			"currency": company_currency,
			"indicator": "Green" if closing_balance >= 0 else "Red",
		},
	]
