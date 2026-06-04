# Copyright (c) 2026, Prime Technology of Bangladesh and contributors
# For license information, please see license.txt

"""
Loyalty Tier Downgrade Logic
=============================

This module provides the scheduled job that automatically checks and downgrades
customer loyalty tiers based on two configurable conditions:

Condition B (Period-Based):
    If a customer hasn't purchased the required minimum maintain amount within
    the evaluation period (Monthly/Quarterly/Yearly), they get downgraded.

Condition C (Inactivity-Based):
    If a customer hasn't made any purchase within a specified number of days,
    they get downgraded.

The downgrade can be either:
    - "One Step Down": Move to the next lower tier
    - "Drop to Lowest": Drop directly to the lowest tier
"""

import frappe
from frappe import _
from frappe.utils import add_months, flt, getdate, now_datetime, today


@frappe.whitelist()
def check_loyalty_tier_downgrade():
	"""
	Main entry point called by the scheduler (daily).
	Reads Loyalty Downgrade Settings and evaluates every enrolled customer.

	Returns a summary message indicating how many customers were downgraded.
	"""
	settings = frappe.get_single("Loyalty Downgrade Settings")

	if not settings.enabled:
		return _("Loyalty Downgrade is disabled.")

	if not settings.loyalty_program or not settings.company:
		frappe.log_error(
			title="Loyalty Downgrade Error",
			message="Loyalty Downgrade Settings is enabled but Loyalty Program or Company is not set.",
		)
		return _("Configuration error: Loyalty Program or Company not set.")

	# Get the tier hierarchy for this loyalty program (sorted by eligibility DESC)
	tiers = get_tier_hierarchy(settings.loyalty_program)
	if not tiers or len(tiers) < 2:
		return _("Loyalty Program must have at least 2 tiers for downgrade to work.")

	# Get all customers enrolled in this loyalty program who are not at the lowest tier
	lowest_tier = tiers[-1]["tier_name"]
	customers = frappe.get_all(
		"Customer",
		filters={
			"loyalty_program": settings.loyalty_program,
			"loyalty_program_tier": ["!=", lowest_tier],
			"loyalty_program_tier": ["is", "set"],
			"disabled": 0,
		},
		fields=["name", "customer_name", "loyalty_program_tier"],
	)

	downgraded_count = 0

	for customer in customers:
		current_tier = customer.loyalty_program_tier

		if not current_tier:
			continue

		# Check if current tier is already the lowest
		if current_tier == lowest_tier:
			continue

		downgrade_reason = None
		detail_message = ""

		# --- Condition B: Period-Based Downgrade ---
		if settings.enable_period_downgrade:
			period_result = check_period_based_downgrade(
				customer=customer.name,
				company=settings.company,
				evaluation_period=settings.evaluation_period,
				maintain_amount=flt(settings.maintain_amount),
			)
			if period_result["should_downgrade"]:
				downgrade_reason = "Period Based"
				detail_message = period_result["detail"]

		# --- Condition C: Inactivity-Based Downgrade ---
		if not downgrade_reason and settings.enable_inactivity_downgrade:
			inactivity_result = check_inactivity_based_downgrade(
				customer=customer.name,
				company=settings.company,
				inactive_days=settings.inactive_days,
			)
			if inactivity_result["should_downgrade"]:
				downgrade_reason = "Inactivity Based"
				detail_message = inactivity_result["detail"]

		# --- Perform Downgrade ---
		if downgrade_reason:
			downgrade_type = (
				settings.period_downgrade_type
				if downgrade_reason == "Period Based"
				else settings.inactivity_downgrade_type
			)

			new_tier = get_downgraded_tier(
				current_tier=current_tier,
				tiers=tiers,
				downgrade_type=downgrade_type,
			)

			if new_tier and new_tier != current_tier:
				perform_downgrade(
					customer=customer.name,
					customer_name=customer.customer_name,
					loyalty_program=settings.loyalty_program,
					previous_tier=current_tier,
					new_tier=new_tier,
					downgrade_reason=downgrade_reason,
					details=detail_message,
				)
				downgraded_count += 1

	message = _("{0} customer(s) downgraded.").format(downgraded_count)
	if downgraded_count == 0:
		message = _("No customers needed downgrading.")

	frappe.logger("loyalty_downgrade").info(message)
	return message


def get_tier_hierarchy(loyalty_program):
	"""
	Returns the tier list sorted by eligibility DESC (highest tier first).

	Args:
		loyalty_program: Name of the Loyalty Program

	Returns:
		List of dicts with 'tier_name' and 'eligibility', sorted highest first.
		Example: [
			{"tier_name": "Gold", "eligibility": 50000},
			{"tier_name": "Silver", "eligibility": 10000},
			{"tier_name": "Bronze", "eligibility": 0}
		]
	"""
	collection_rules = frappe.get_all(
		"Loyalty Program Collection",
		filters={"parent": loyalty_program, "parenttype": "Loyalty Program"},
		fields=["tier_name", "eligibility"],
		order_by="eligibility desc",
	)

	return [{"tier_name": r.tier_name, "eligibility": flt(r.eligibility)} for r in collection_rules]


def check_period_based_downgrade(customer, company, evaluation_period, maintain_amount):
	"""
	Check if the customer has met the minimum purchase amount within the evaluation period.

	Args:
		customer: Customer name
		company: Company name
		evaluation_period: "Monthly", "Quarterly", or "Yearly"
		maintain_amount: Minimum purchase amount required

	Returns:
		dict with 'should_downgrade' (bool) and 'detail' (str)
	"""
	period_months = {"Monthly": 1, "Quarterly": 3, "Yearly": 12}
	months = period_months.get(evaluation_period, 1)

	from_date = add_months(today(), -months)
	to_date = today()

	# Sum of submitted Sales Invoice grand_total in the period
	total_purchased = frappe.db.sql(
		"""
		SELECT COALESCE(SUM(grand_total), 0)
		FROM `tabSales Invoice`
		WHERE customer = %s
			AND company = %s
			AND docstatus = 1
			AND is_return = 0
			AND posting_date BETWEEN %s AND %s
		""",
		(customer, company, from_date, to_date),
	)

	total_purchased = flt(total_purchased[0][0]) if total_purchased else 0

	should_downgrade = total_purchased < maintain_amount

	detail = (
		"Period: {period} ({from_date} to {to_date}). "
		"Purchased: {currency}{purchased:,.2f}. "
		"Required: {currency}{required:,.2f}."
	).format(
		period=evaluation_period,
		from_date=from_date,
		to_date=to_date,
		purchased=total_purchased,
		required=maintain_amount,
		currency="",
	)

	return {"should_downgrade": should_downgrade, "detail": detail}


def check_inactivity_based_downgrade(customer, company, inactive_days):
	"""
	Check if the customer has been inactive (no purchases) for more than the threshold days.

	Args:
		customer: Customer name
		company: Company name
		inactive_days: Maximum allowed inactive days

	Returns:
		dict with 'should_downgrade' (bool) and 'detail' (str)
	"""
	last_invoice_date = frappe.db.sql(
		"""
		SELECT MAX(posting_date)
		FROM `tabSales Invoice`
		WHERE customer = %s
			AND company = %s
			AND docstatus = 1
			AND is_return = 0
		""",
		(customer, company),
	)

	last_invoice_date = last_invoice_date[0][0] if last_invoice_date and last_invoice_date[0][0] else None

	if not last_invoice_date:
		# No invoices at all — should not have a tier, but if they do, downgrade
		detail = "No purchase history found. Threshold: {0} days.".format(inactive_days)
		return {"should_downgrade": True, "detail": detail}

	days_since_purchase = (getdate(today()) - getdate(last_invoice_date)).days
	should_downgrade = days_since_purchase > inactive_days

	detail = (
		"Last purchase: {last_date} ({days} days ago). "
		"Threshold: {threshold} days."
	).format(
		last_date=last_invoice_date,
		days=days_since_purchase,
		threshold=inactive_days,
	)

	return {"should_downgrade": should_downgrade, "detail": detail}


def get_downgraded_tier(current_tier, tiers, downgrade_type):
	"""
	Determine the new tier after downgrade.

	Args:
		current_tier: Current tier name
		tiers: List of tier dicts sorted by eligibility DESC
		downgrade_type: "One Step Down" or "Drop to Lowest"

	Returns:
		New tier name, or None if cannot downgrade further.
	"""
	tier_names = [t["tier_name"] for t in tiers]

	if current_tier not in tier_names:
		# Current tier not found in the program (possibly renamed)
		return None

	current_index = tier_names.index(current_tier)
	lowest_index = len(tier_names) - 1

	if current_index >= lowest_index:
		# Already at the lowest tier
		return None

	if downgrade_type == "Drop to Lowest":
		return tier_names[lowest_index]
	else:
		# One Step Down — move to the next tier in the sorted list
		return tier_names[current_index + 1]


def perform_downgrade(customer, customer_name, loyalty_program, previous_tier, new_tier, downgrade_reason, details):
	"""
	Execute the tier downgrade: update customer record and create audit log.

	Args:
		customer: Customer name (ID)
		customer_name: Customer display name
		loyalty_program: Loyalty Program name
		previous_tier: Tier before downgrade
		new_tier: Tier after downgrade
		downgrade_reason: "Period Based" or "Inactivity Based"
		details: Human-readable detail string
	"""
	# Update customer's loyalty tier
	frappe.db.set_value("Customer", customer, "loyalty_program_tier", new_tier)

	# Create audit log
	log = frappe.get_doc(
		{
			"doctype": "Loyalty Downgrade Log",
			"customer": customer,
			"customer_name": customer_name,
			"loyalty_program": loyalty_program,
			"previous_tier": previous_tier,
			"new_tier": new_tier,
			"downgrade_reason": downgrade_reason,
			"details": details,
			"downgrade_date": today(),
		}
	)
	log.flags.ignore_permissions = True
	log.insert()

	frappe.logger("loyalty_downgrade").info(
		"Downgraded customer {customer} ({customer_name}) from '{previous}' to '{new}' — Reason: {reason}".format(
			customer=customer,
			customer_name=customer_name,
			previous=previous_tier,
			new=new_tier,
			reason=downgrade_reason,
		)
	)
