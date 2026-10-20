# Copyright (c) 2026, Prime Technology of Bangladesh and contributors
# For license information, please see license.txt

"""
Loyalty Program Auto-Assignment
================================

Automatically assigns a Loyalty Program to a Customer when they become eligible,
triggered on Sales Invoice submission.

Tier Upgrade Logic:
-------------------
1. YEARLY UPGRADE (2nd, 3rd tier etc.):
   If `yearly_upgrade_amount` > 0 on a collection rule, the customer must have
   spent that amount cumulatively over the Rolling 12 months to reach that tier.
   Highest matching tier wins.

2. MONTHLY CHECKPOINT (1st tier activation):
   If `tier_enable_amount` > 0 on a collection rule, the customer must spend
   at least that amount in the current calendar month to activate that tier.

3. ERPNext STANDARD FALLBACK:
   If neither custom field is set, falls back to ERPNext's standard `min_spent`
   (lifetime total spend) logic.

Points are earned on the *excess* net_total above the monthly checkpoint amount
(excluding tax and shipping). ERPNext's built-in point creation is suppressed
via dont_create_loyalty_points=1 and replaced by create_custom_loyalty_point_entry().
"""

import frappe
from frappe import _
from frappe.utils import today

from erpnext.selling.doctype.customer.customer import get_loyalty_programs


# ─────────────────────────────────────────────────────────────────────────────
# Hook: before_submit
# ─────────────────────────────────────────────────────────────────────────────

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
		# Update customer's tier evaluation based on current spend (including this invoice)
		_set_customer_tier(doc.customer, customer.loyalty_program, doc.company, current_doc=doc)
		return

	# Check for eligible loyalty programs (uses ERPNext's built-in logic)
	eligible_programs = get_loyalty_programs(customer)

	if not eligible_programs:
		return

	if len(eligible_programs) == 1:
		loyalty_program_name = eligible_programs[0]
	else:
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

	# Calculate and set the correct tier based on total spend (including this invoice)
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


# ─────────────────────────────────────────────────────────────────────────────
# Spend Helpers
# ─────────────────────────────────────────────────────────────────────────────

def get_month_to_date_spend(customer, company, current_doc=None):
	"""
	Customer-এর চলতি মাসের (1st to today) মোট নেট খরচ হিসাব করে।
	current_doc এর net_total ও অন্তর্ভুক্ত করা হয়।
	"""
	from frappe.utils import flt, get_first_day

	start_of_month = get_first_day(today())
	current_name = current_doc.name if (current_doc and hasattr(current_doc, "name") and not current_doc.is_new()) else ""

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

	if current_doc and not getattr(current_doc, "is_return", False):
		total_spend += flt(getattr(current_doc, "net_total", 0))

	return total_spend


def get_yearly_spend(customer, company, current_doc=None):
	"""
	Customer-এর Rolling 12 months (আজ থেকে ঠিক ১ বছর পিছনে) মোট নেট খরচ।
	current_doc এর net_total ও অন্তর্ভুক্ত করা হয়।
	২য়, ৩য় Tier আপগ্রেড চেকের জন্য ব্যবহৃত হয়।
	"""
	from frappe.utils import add_years, flt

	one_year_ago = add_years(today(), -1)
	current_name = current_doc.name if (current_doc and hasattr(current_doc, "name") and not current_doc.is_new()) else ""

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
		(customer, company, one_year_ago, today(), current_name),
	)

	total = flt(res[0][0]) if res and res[0] else 0.0

	if current_doc and not getattr(current_doc, "is_return", False):
		total += flt(getattr(current_doc, "net_total", 0))

	return total


# ─────────────────────────────────────────────────────────────────────────────
# Tier Calculation
# ─────────────────────────────────────────────────────────────────────────────

def _set_customer_tier(customer, loyalty_program_name, company, current_doc=None):
	"""
	Customer-এর Loyalty Tier নির্ধারণ ও আপডেট করে।

	Priority:
	  1. yearly_upgrade_amount > 0  → Rolling 12-month spend চেক (২য়, ৩য় Tier)
	  2. tier_enable_amount > 0     → Current month spend চেক (১ম Tier)
	  3. ERPNext standard fallback  → min_spent (lifetime total)

	Tier পরিবর্তন হলে:
	  • Loyalty Tier Upgrade Log তৈরি হয়
	  • SMS + Email + In-App Notification পাঠানো হয়
	"""
	from frappe.utils import flt

	try:
		old_tier = frappe.db.get_value("Customer", customer, "loyalty_program_tier")
		active_tier = None
		upgrade_reason = None

		# সমস্ত collection rules নিয়ে আসা — eligibility DESC তে সর্টেড
		collection_rules = frappe.get_all(
			"Loyalty Program Collection",
			filters={"parent": loyalty_program_name, "parenttype": "Loyalty Program"},
			fields=["tier_name", "tier_enable_amount", "yearly_upgrade_amount", "min_spent", "eligibility"],
			order_by="eligibility desc, yearly_upgrade_amount desc, tier_enable_amount desc",
		)

		# ── Step 1: Yearly Upgrade Check (2nd, 3rd Tier) ──────────────────────
		yearly_rules = [r for r in collection_rules if flt(r.get("yearly_upgrade_amount")) > 0]
		if yearly_rules:
			yearly_spend = get_yearly_spend(customer, company, current_doc=current_doc)
			for rule in yearly_rules:
				if yearly_spend >= flt(rule.get("yearly_upgrade_amount")):
					active_tier = rule.get("tier_name")
					upgrade_reason = "Yearly Spend Upgrade"
					break

		# ── Step 2: Monthly Checkpoint (1st Tier Activation) ──────────────────
		if not active_tier:
			monthly_rules = [r for r in collection_rules if flt(r.get("tier_enable_amount")) > 0]
			if monthly_rules:
				month_spend = get_month_to_date_spend(customer, company, current_doc=current_doc)
				for rule in monthly_rules:
					if month_spend >= flt(rule.get("tier_enable_amount")):
						active_tier = rule.get("tier_name")
						upgrade_reason = "Monthly Spend Checkpoint"
						break

		# ── Step 3: ERPNext standard fallback ─────────────────────────────────
		if not active_tier:
			from erpnext.accounts.doctype.loyalty_program.loyalty_program import (
				get_loyalty_program_details_with_points,
			)
			lp_details = get_loyalty_program_details_with_points(
				customer,
				loyalty_program=loyalty_program_name,
				company=company,
				include_expired_entry=True,
			)
			if lp_details and lp_details.get("tier_name"):
				active_tier = lp_details.tier_name
				upgrade_reason = "Monthly Spend Checkpoint"

		# ── Apply Tier Change ──────────────────────────────────────────────────
		if active_tier and active_tier != old_tier:
			frappe.db.set_value("Customer", customer, "loyalty_program_tier", active_tier)

			_log_tier_upgrade(
				customer=customer,
				loyalty_program=loyalty_program_name,
				previous_tier=old_tier or "None",
				new_tier=active_tier,
				upgrade_reason=upgrade_reason,
				triggered_by=current_doc.name if (current_doc and not current_doc.is_new()) else None,
			)

			_send_tier_change_notification(
				customer=customer,
				loyalty_program=loyalty_program_name,
				previous_tier=old_tier or "None",
				new_tier=active_tier,
				change_type="Upgrade",
			)

		elif active_tier and not old_tier:
			# প্রথমবার tier সেট — upgrade নয়, প্রথম enrollment
			frappe.db.set_value("Customer", customer, "loyalty_program_tier", active_tier)
			_log_tier_upgrade(
				customer=customer,
				loyalty_program=loyalty_program_name,
				previous_tier="None",
				new_tier=active_tier,
				upgrade_reason=upgrade_reason or "Monthly Spend Checkpoint",
				triggered_by=current_doc.name if (current_doc and not current_doc.is_new()) else None,
			)

	except Exception:
		frappe.log_error(
			title="Loyalty Auto-Assign Tier Error",
			message=frappe.get_traceback(),
		)


# ─────────────────────────────────────────────────────────────────────────────
# Logging & Notifications
# ─────────────────────────────────────────────────────────────────────────────

def _log_tier_upgrade(customer, loyalty_program, previous_tier, new_tier, upgrade_reason, triggered_by=None):
	"""
	Loyalty Tier Upgrade Log (LUL-XXXX) তৈরি করে।
	প্রতিটি Tier পরিবর্তনের অডিট ট্রেইল রাখে।
	"""
	try:
		log = frappe.get_doc({
			"doctype": "Loyalty Tier Upgrade Log",
			"customer": customer,
			"loyalty_program": loyalty_program,
			"upgrade_date": today(),
			"previous_tier": previous_tier or "None",
			"new_tier": new_tier,
			"upgrade_reason": upgrade_reason,
			"triggered_by_invoice": triggered_by,
			"details": f"Tier changed: '{previous_tier}' → '{new_tier}'. Reason: {upgrade_reason}.",
		})
		log.flags.ignore_permissions = True
		log.insert()
	except Exception:
		frappe.log_error(title="Loyalty Tier Upgrade Log Error", message=frappe.get_traceback())


def _send_tier_change_notification(customer, loyalty_program, previous_tier, new_tier, change_type="Upgrade"):
	"""
	Tier পরিবর্তনে কাস্টমারকে SMS + Email পাঠায় এবং
	Internal Users-কে In-App নোটিফিকেশন দেয়।

	change_type: "Upgrade" অথবা "Downgrade"
	"""
	try:
		settings = frappe.get_single("Loyalty Tier Upgrade Settings")

		if change_type == "Upgrade" and not settings.get("enable_upgrade_notification"):
			return
		if change_type == "Downgrade" and not settings.get("enable_downgrade_notification"):
			return

		customer_doc = frappe.get_doc("Customer", customer)
		customer_email = customer_doc.get("email_id")
		customer_mobile = customer_doc.get("mobile_no")
		customer_name = customer_doc.customer_name

		emoji = "🎉" if change_type == "Upgrade" else "⬇️"
		subject = _("{emoji} Loyalty Tier {change_type}: {prev} → {new}").format(
			emoji=emoji,
			change_type=change_type,
			prev=previous_tier,
			new=new_tier,
		)

		html_message = _(
			"<p>Dear <b>{name}</b>,</p>"
			"<p>Your loyalty tier in <b>{program}</b> has been <b>{action}</b>!</p>"
			"<table cellpadding='8' border='0'>"
			"<tr><td><b>Previous Tier:</b></td><td>{prev}</td></tr>"
			"<tr><td><b>New Tier:</b></td><td><b>{new}</b></td></tr>"
			"</table>"
			"<p>Thank you for your continued loyalty!</p>"
		).format(
			name=customer_name,
			program=loyalty_program,
			action="upgraded" if change_type == "Upgrade" else "downgraded",
			prev=previous_tier,
			new=new_tier,
		)

		sms_message = _(
			"Dear {name}, your Loyalty Tier has been {action} "
			"from {prev} to {new} in {program}. Thank you!"
		).format(
			name=customer_name,
			action="upgraded" if change_type == "Upgrade" else "downgraded",
			prev=previous_tier,
			new=new_tier,
			program=loyalty_program,
		)

		# ── SMS ───────────────────────────────────────────────────────────────
		if settings.get("notify_customer_sms") and customer_mobile:
			try:
				from frappe.core.doctype.sms_settings.sms_settings import send_sms
				send_sms(receiver_list=[customer_mobile], msg=sms_message, success_msg=False)
			except Exception:
				frappe.log_error(title="Loyalty SMS Notification Error", message=frappe.get_traceback())

		# ── Email ─────────────────────────────────────────────────────────────
		if settings.get("notify_customer_email") and customer_email:
			frappe.sendmail(recipients=[customer_email], subject=subject, message=html_message)

		# ── In-App (Internal Users) ───────────────────────────────────────────
		if settings.get("notify_internal_users"):
			roles = ["Sales Manager", "Accounts Manager"]
			users = frappe.get_all(
				"Has Role",
				filters={"role": ["in", roles], "parenttype": "User"},
				pluck="parent",
			)
			for user in set(users):
				try:
					frappe.get_doc({
						"doctype": "Notification Log",
						"subject": subject,
						"email_content": html_message,
						"for_user": user,
						"type": "Alert",
						"document_type": "Customer",
						"document_name": customer,
					}).insert(ignore_permissions=True)
				except Exception:
					pass

	except Exception:
		frappe.log_error(title="Loyalty Tier Notification Error", message=frappe.get_traceback())


# ─────────────────────────────────────────────────────────────────────────────
# Override: get_loyalty_program_details_with_points
# ─────────────────────────────────────────────────────────────────────────────

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
	Override ERPNext's standard get_loyalty_program_details_with_points.

	Priority:
	  1. yearly_upgrade_amount rules  → Rolling 12-month spend
	  2. tier_enable_amount rules     → Current month spend
	  3. ERPNext standard min_spent   → Lifetime spend
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

	collection_rules = [d.as_dict() for d in loyalty_program_doc.collection_rules]

	# ── Step 1: Yearly upgrade rules ──────────────────────────────────────
	yearly_rules = [r for r in collection_rules if flt(r.get("yearly_upgrade_amount")) > 0]
	if yearly_rules:
		yearly_spend = get_yearly_spend(customer, company) + flt(current_transaction_amount)
		sorted_yearly = sorted(yearly_rules, key=lambda r: flt(r.get("yearly_upgrade_amount")), reverse=True)
		matched = None
		for rule in sorted_yearly:
			if yearly_spend >= flt(rule.get("yearly_upgrade_amount")):
				matched = rule
				break
		if matched:
			lp_details.tier_name = matched["tier_name"]
			lp_details.collection_factor = matched["collection_factor"]
		else:
			# Fall to monthly check
			yearly_rules = []  # reset to continue below

	# ── Step 2: Monthly checkpoint rules ──────────────────────────────────
	if not yearly_rules:
		monthly_rules = [r for r in collection_rules if flt(r.get("tier_enable_amount")) > 0]
		if monthly_rules:
			month_spend = get_month_to_date_spend(customer, company) + flt(current_transaction_amount)
			sorted_monthly = sorted(monthly_rules, key=lambda r: flt(r.get("tier_enable_amount")), reverse=True)
			matched_monthly = None
			for rule in sorted_monthly:
				if month_spend >= flt(rule.get("tier_enable_amount")):
					matched_monthly = rule
					break
			if matched_monthly:
				lp_details.tier_name = matched_monthly["tier_name"]
				lp_details.collection_factor = matched_monthly["collection_factor"]
			else:
				# Fallback to lowest tier
				lowest = sorted(monthly_rules, key=lambda r: flt(r.get("tier_enable_amount")))[0]
				lp_details.tier_name = lowest["tier_name"]
				lp_details.collection_factor = lowest["collection_factor"]

		else:
			# ── Step 3: ERPNext standard min_spent ────────────────────────
			tier_spent_level = sorted(collection_rules, key=lambda r: flt(r.get("min_spent", 0)))
			for i, d in enumerate(tier_spent_level):
				if i == 0 or (flt(lp_details.get("total_spent")) + flt(current_transaction_amount)) >= flt(d.get("min_spent", 0)):
					lp_details.tier_name = d["tier_name"]
					lp_details.collection_factor = d["collection_factor"]
				else:
					break

	return lp_details


# ─────────────────────────────────────────────────────────────────────────────
# Hook: on_submit
# ─────────────────────────────────────────────────────────────────────────────

def create_custom_loyalty_point_entry(doc, method):
	"""
	Hook: Sales Invoice → on_submit

	Loyalty Point Calculation Logic:
	  1. Lifetime 1st Qualifying Invoice:
	     When a customer reaches the activation checkpoint (e.g. 10,000 BDT) for the
	     first time in their life, points are calculated ONLY on the EXCESS net_total
	     above that checkpoint (e.g. 16,400 - 10,000 = 6,400 BDT).
	  2. Subsequent Invoices:
	     Once the customer has earned points at least once, every subsequent invoice
	     earns points on its full eligible net_total (based on the tier's collection factor).
	"""
	if doc.is_return or doc.docstatus != 1 or not doc.loyalty_program:
		return

	from frappe.utils import add_days, cint, flt

	# Fetch active tier details respecting tier_enable_amount / yearly_upgrade_amount
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

	collection_factor = flt(lp_details.get("collection_factor") or 0.0)
	if collection_factor <= 0:
		# Tier doesn't earn points (e.g. collection_factor = 0 in Silver)
		_set_customer_tier(doc.customer, doc.loyalty_program, doc.company, current_doc=doc)
		return

	loyalty_program_doc = frappe.get_doc("Loyalty Program", doc.loyalty_program)

	# Net amount of current invoice (after discounts, excluding tax and shipping)
	current_invoice_net = flt(doc.net_total) - flt(doc.get("loyalty_amount") or 0)

	# Check if customer has ever earned loyalty points in any previous entry
	has_prior_points = frappe.db.exists(
		"Loyalty Point Entry",
		{
			"customer": doc.customer,
			"loyalty_points": [">", 0],
			"invoice": ["!=", doc.name],
		},
	)

	if not has_prior_points:
		# ── 1ST QUALIFYING INVOICE IN CUSTOMER'S LIFE ─────────────────────────
		# Points are strictly earned on the EXCESS amount above the activation checkpoint
		checkpoint_rules = [
			flt(r.tier_enable_amount)
			for r in loyalty_program_doc.collection_rules
			if flt(r.tier_enable_amount) > 0
		]
		initial_checkpoint = min(checkpoint_rules) if checkpoint_rules else 0.0

		if current_invoice_net >= initial_checkpoint:
			eligible_net_amount = max(0.0, current_invoice_net - initial_checkpoint)
		else:
			eligible_net_amount = 0.0
	else:
		# ── SUBSEQUENT INVOICES ───────────────────────────────────────────────
		# Once activated, customer earns points on full net spend of each purchase
		eligible_net_amount = max(0.0, current_invoice_net)

	if eligible_net_amount > 0:
		points_earned = cint(eligible_net_amount / collection_factor)

		if points_earned > 0:
			lpe = frappe.get_doc({
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
			})
			lpe.flags.ignore_permissions = True
			lpe.insert()

	# Ensure customer tier is updated to active_tier after submission
	_set_customer_tier(doc.customer, doc.loyalty_program, doc.company, current_doc=doc)

