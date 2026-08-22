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
		# Update customer's tier evaluation based on current month spend (including this invoice)
		_set_customer_tier(doc.customer, customer.loyalty_program, doc.company, current_doc=doc)
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

	# Now calculate and set the correct tier based on total spend (including this invoice)
	_set_customer_tier(doc.customer, loyalty_program_name, doc.company, current_doc=doc)

	# Crucial: update the Sales Invoice document before it submits so points are added!
	doc.loyalty_program = loyalty_program_name
	doc.db_set("loyalty_program", loyalty_program_name)
	doc.dont_create_loyalty_points = 1
	doc.db_set("dont_create_loyalty_points", 1)

	frappe.msgprint(
		_("Loyalty Program <b>{0}</b> has been automatically assigned to customer <b>{1}</b>").format(
			loyalty_program_name, customer.customer_name
		),
		alert=True,
		indicator="green",
	)


def get_month_to_date_spend(customer, company, current_doc=None):
	"""
	Calculate customer's total Sales Invoice net_total (excluding taxes & shipping)
	for the current calendar month (1st of current month to today).
	"""
	from frappe.utils import flt, get_first_day, today

	start_of_month = get_first_day(today())
	current_name = current_doc.name if (current_doc and hasattr(current_doc, "name")) else ""

	res = frappe.db.sql(
		"""
		SELECT COALESCE(SUM(net_total), 0)
		FROM `tabSales Invoice`
		WHERE customer = %s
			AND company = %s
			AND docstatus = 1
			AND is_return = 0
			AND posting_date BETWEEN %s AND %s
			AND name != %s
		""",
		(customer, company, start_of_month, today(), current_name),
	)

	total_spend = flt(res[0][0]) if res and res[0] else 0.0

	# Include current invoice's net_total if provided and not return
	if current_doc and not getattr(current_doc, "is_return", False):
		total_spend += flt(getattr(current_doc, "net_total", 0))

	return total_spend


def _set_customer_tier(customer, loyalty_program_name, company, current_doc=None):
	"""
	Calculate and set the customer's loyalty tier.
	First checks custom `tier_enable_amount` (Check Point) rules based on month-to-date net spend.
	Falls back to ERPNext's standard total spend tier calculation.
	"""
	from erpnext.accounts.doctype.loyalty_program.loyalty_program import (
		get_loyalty_program_details_with_points,
	)
	from frappe.utils import flt

	try:
		# 1. Fetch collection rules for this loyalty program sorted by tier requirement DESC
		collection_rules = frappe.get_all(
			"Loyalty Program Collection",
			filters={"parent": loyalty_program_name, "parenttype": "Loyalty Program"},
			fields=["tier_name", "min_spent", "tier_enable_amount"],
			order_by="tier_enable_amount desc, min_spent desc",
		)

		month_spend = get_month_to_date_spend(customer, company, current_doc=current_doc)
		active_tier = None

		# Check if customer meets any Tier Enable Checkpoint based on current month purchase
		for rule in collection_rules:
			enable_amount = flt(rule.get("tier_enable_amount"))
			if enable_amount > 0 and month_spend >= enable_amount:
				active_tier = rule.get("tier_name")
				break

		# 2. If no custom tier_enable_amount checkpoint matched, fallback to ERPNext standard calculation
		if not active_tier:
			lp_details = get_loyalty_program_details_with_points(
				customer,
				loyalty_program=loyalty_program_name,
				company=company,
				include_expired_entry=True,
			)
			if lp_details and lp_details.get("tier_name"):
				active_tier = lp_details.tier_name

		if active_tier:
			frappe.db.set_value("Customer", customer, "loyalty_program_tier", active_tier)

	except Exception:
		frappe.log_error(
			title="Loyalty Auto-Assign Tier Error",
			message=frappe.get_traceback(),
		)


@frappe.whitelist()
def custom_get_loyalty_program_details_with_points(
	customer,
	loyalty_program=None,
	expiry_date=None,
	company=None,
	silent=False,
	include_expired_entry=False,
	current_transaction_amount=0,
):
	"""
	Override ERPNext's standard get_loyalty_program_details_with_points function.
	Respects custom `tier_enable_amount` checkpoints when evaluating tiers.
	"""
	from erpnext.accounts.doctype.loyalty_program.loyalty_program import (
		get_loyalty_program_details,
		get_loyalty_details,
	)
	from frappe.utils import flt

	lp_details = get_loyalty_program_details(customer, loyalty_program, company=company, silent=silent)
	loyalty_program_doc = frappe.get_doc("Loyalty Program", loyalty_program)
	loyalty_details = get_loyalty_details(
		customer, loyalty_program_doc.name, expiry_date, company, include_expired_entry
	)
	lp_details.update(loyalty_details)

	# Check if any collection rule has tier_enable_amount > 0
	has_custom_enable_amount = any(flt(rule.get("tier_enable_amount")) > 0 for rule in loyalty_program_doc.collection_rules)

	if has_custom_enable_amount:
		# Calculate month-to-date net spend (including current_transaction_amount)
		month_spend = get_month_to_date_spend(customer, company) + flt(current_transaction_amount)

		# Sort rules by tier_enable_amount DESC
		sorted_rules = sorted(
			[d.as_dict() for d in loyalty_program_doc.collection_rules],
			key=lambda rule: flt(rule.get("tier_enable_amount") or 0),
			reverse=True,
		)

		matched_rule = None
		for rule in sorted_rules:
			enable_amt = flt(rule.get("tier_enable_amount"))
			if enable_amt > 0 and month_spend >= enable_amt:
				matched_rule = rule
				break

		if matched_rule:
			lp_details.tier_name = matched_rule.tier_name
			lp_details.collection_factor = matched_rule.collection_factor
		else:
			# Fallback to lowest tier if spend hasn't reached any enable_amount
			lowest_rule = sorted_rules[-1]
			lp_details.tier_name = lowest_rule.tier_name
			lp_details.collection_factor = lowest_rule.collection_factor
	else:
		# Standard ERPNext logic (sorted by min_spent)
		tier_spent_level = sorted(
			[d.as_dict() for d in loyalty_program_doc.collection_rules],
			key=lambda rule: rule.min_spent,
		)
		for i, d in enumerate(tier_spent_level):
			if i == 0 or (lp_details.total_spent + current_transaction_amount) >= d.min_spent:
				lp_details.tier_name = d.tier_name
				lp_details.collection_factor = d.collection_factor
			else:
				break

	return lp_details


def create_custom_loyalty_point_entry(doc, method):
	"""
	Hook: Sales Invoice -> on_submit
	Creates Loyalty Point Entry calculating points strictly on the excess net_total above tier_enable_amount.
	Excludes shipping, taxes, and initial checkpoint amounts.
	"""
	if doc.is_return or doc.docstatus != 1 or not doc.loyalty_program:
		return

	from frappe.utils import add_days, cint, flt

	# Fetch active tier details respecting tier_enable_amount
	lp_details = custom_get_loyalty_program_details_with_points(
		doc.customer,
		loyalty_program=doc.loyalty_program,
		company=doc.company,
		expiry_date=doc.posting_date,
		include_expired_entry=True,
		current_transaction_amount=flt(doc.net_total),
	)

	if not lp_details:
		return

	loyalty_program_doc = frappe.get_doc("Loyalty Program", doc.loyalty_program)
	active_tier_name = lp_details.get("tier_name")

	# Find collection rule for the active tier
	matched_rule = None
	for rule in loyalty_program_doc.collection_rules:
		if rule.tier_name == active_tier_name:
			matched_rule = rule
			break

	tier_enable_amount = flt(matched_rule.get("tier_enable_amount")) if matched_rule else 0.0

	# Prior net spend in current month (excluding this invoice)
	prior_net_spend = get_month_to_date_spend(doc.customer, doc.company, current_doc=None)

	needed_checkpoint_amount = max(0.0, tier_enable_amount - prior_net_spend)

	# Net amount of current invoice after deducting discounts (excludes tax and shipping)
	current_invoice_net = flt(doc.net_total) - flt(doc.get("loyalty_amount") or 0)

	# Excess net amount eligible for points
	eligible_net_amount = max(0.0, current_invoice_net - needed_checkpoint_amount)

	if eligible_net_amount > 0:
		collection_factor = flt(lp_details.get("collection_factor")) or 1.0
		points_earned = cint(eligible_net_amount / collection_factor)

		if points_earned > 0:
			lpe = frappe.get_doc(
				{
					"doctype": "Loyalty Point Entry",
					"company": doc.company,
					"loyalty_program": lp_details.loyalty_program,
					"loyalty_program_tier": lp_details.tier_name,
					"customer": doc.customer,
					"invoice_type": doc.doctype,
					"invoice": doc.name,
					"loyalty_points": points_earned,
					"purchase_amount": eligible_net_amount,
					"expiry_date": add_days(doc.posting_date, lp_details.expiry_duration),
					"posting_date": doc.posting_date,
				}
			)
			lpe.flags.ignore_permissions = 1
			lpe.insert()

	# Ensure customer tier is updated to active_tier
	_set_customer_tier(doc.customer, doc.loyalty_program, doc.company, current_doc=doc)




