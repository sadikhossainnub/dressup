# Copyright (c) 2026, Prime Technology of Bangladesh and contributors
# For license information, please see license.txt

"""
Loyalty Program Auto-Assignment
================================

Automatically assigns a Loyalty Program to a Customer when they become eligible,
triggered on Sales Invoice submission.

ERPNext's built-in `set_loyalty_program()` on Customer only runs during Customer
validate (save). This means if a customer was created before a Loyalty Program
existed, or if their customer group/territory changes, they won't get enrolled
until someone manually saves the Customer again.

This hook solves that by checking eligibility on every Sales Invoice submit and
auto-assigning the program + calculating the correct tier.
"""

import frappe
from frappe import _
from frappe.utils import today

from erpnext.selling.doctype.customer.customer import get_loyalty_programs


def auto_assign_loyalty_program(doc, method):
	"""
	Hook: Sales Invoice → before_submit

	If the customer doesn't have a loyalty program assigned, check if they
	are eligible for one (auto_opt_in programs matching customer_group/territory).
	If eligible, assign the program to the customer and update the Sales Invoice
	document so points are correctly calculated on submission.
	"""
	if doc.is_return:
		return

	customer = frappe.get_doc("Customer", doc.customer)

	if customer.loyalty_program:
		# Already enrolled — make sure Sales Invoice has it set too just in case
		if not doc.loyalty_program:
			doc.loyalty_program = customer.loyalty_program
			doc.db_set("loyalty_program", customer.loyalty_program)
		return

	# Check for eligible loyalty programs (uses ERPNext's built-in logic)
	eligible_programs = get_loyalty_programs(customer)

	if not eligible_programs:
		return

	if len(eligible_programs) == 1:
		loyalty_program_name = eligible_programs[0]
	else:
		# Multiple programs found — pick the first one and log a note
		loyalty_program_name = eligible_programs[0]
		frappe.msgprint(
			_("Multiple Loyalty Programs found for {0}. Auto-assigned: {1}").format(
				frappe.bold(customer.customer_name),
				frappe.bold(loyalty_program_name),
			),
			alert=True,
			indicator="blue",
		)

	# Assign the loyalty program to the customer
	frappe.db.set_value("Customer", doc.customer, "loyalty_program", loyalty_program_name)

	# Now calculate and set the correct tier based on total spend
	_set_customer_tier(doc.customer, loyalty_program_name, doc.company)

	# Crucial: update the Sales Invoice document before it submits so points are added!
	doc.loyalty_program = loyalty_program_name
	doc.db_set("loyalty_program", loyalty_program_name)

	frappe.msgprint(
		_("Loyalty Program <b>{0}</b> has been automatically assigned to customer <b>{1}</b>").format(
			loyalty_program_name, customer.customer_name
		),
		alert=True,
		indicator="green",
	)


def _set_customer_tier(customer, loyalty_program_name, company):
	"""
	Calculate and set the customer's loyalty tier based on their total spend.
	"""
	from erpnext.accounts.doctype.loyalty_program.loyalty_program import (
		get_loyalty_program_details_with_points,
	)

	try:
		lp_details = get_loyalty_program_details_with_points(
			customer,
			loyalty_program=loyalty_program_name,
			company=company,
			include_expired_entry=True,
		)

		if lp_details and lp_details.get("tier_name"):
			frappe.db.set_value(
				"Customer", customer, "loyalty_program_tier", lp_details.tier_name
			)
	except Exception:
		frappe.log_error(
			title="Loyalty Auto-Assign Tier Error",
			message=frappe.get_traceback(),
		)
