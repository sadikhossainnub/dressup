# Dress Up Loyalty Program Module

import frappe


def get_loyalty_program():
	"""
	System-এ active Loyalty Program fetch করে।
	যেকোনো নামের Loyalty Program support করবে।
	"""
	program = frappe.db.get_value(
		"Loyalty Program",
		filters={"auto_opt_in": 1},
		fieldname="name",
	)

	if not program:
		# auto_opt_in না থাকলে যেকোনো active program নাও
		program = frappe.db.get_value(
			"Loyalty Program",
			filters={},
			fieldname="name",
			order_by="creation desc",
		)

	return program


def get_eligibility_threshold(program_name=None):
	"""
	Loyalty Program থেকে eligibility threshold fetch করে।
	0 বা None মানে কোনো threshold নেই (সবাই eligible)।
	"""
	if not program_name:
		program_name = get_loyalty_program()

	if not program_name:
		return 0

	threshold = frappe.db.get_value(
		"Loyalty Program", program_name, "eligibility_threshold"
	)

	return threshold or 0


def get_tier_order(program_name):
	"""
	Loyalty Program-এর tiers ascending order-এ (min_spent অনুযায়ী) return করে।
	প্রতিটি tier-এর সাথে min_spent ও max_spent info ও আসবে।
	যেকোনো tier নাম support করবে।
	"""
	if not program_name:
		return []

	tiers = frappe.get_all(
		"Loyalty Program Collection",
		filters={"parent": program_name, "parenttype": "Loyalty Program"},
		fields=["tier_name", "min_spent", "max_spent"],
		order_by="min_spent asc",
	)

	return [t.tier_name for t in tiers]


def get_tiers_with_range(program_name):
	"""
	Tier list with min/max amount range return করে।
	Returns: [{"tier_name": "Bronze", "min_spent": 0, "max_spent": 50000}, ...]
	"""
	if not program_name:
		return []

	tiers = frappe.get_all(
		"Loyalty Program Collection",
		filters={"parent": program_name, "parenttype": "Loyalty Program"},
		fields=["tier_name", "min_spent", "max_spent"],
		order_by="min_spent asc",
	)

	return tiers


def get_tier_for_amount(program_name, total_spent):
	"""
	Total spent amount অনুযায়ী সঠিক tier return করে।
	min_spent এবং max_spent range check করে।
	"""
	tiers = get_tiers_with_range(program_name)

	if not tiers:
		return None

	matched_tier = tiers[0].tier_name  # default: lowest tier

	for tier in tiers:
		min_amt = tier.min_spent or 0
		max_amt = tier.max_spent or 0

		if max_amt > 0:
			# max_spent set আছে → range check
			if min_amt <= total_spent <= max_amt:
				matched_tier = tier.tier_name
		else:
			# max_spent 0 মানে unlimited (highest tier)
			if total_spent >= min_amt:
				matched_tier = tier.tier_name

	return matched_tier


def get_lowest_tier(program_name):
	"""Program-এর সবচেয়ে lowest tier return করে।"""
	tiers = get_tier_order(program_name)
	return tiers[0] if tiers else None
