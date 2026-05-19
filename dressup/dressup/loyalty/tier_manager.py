# dressup/dressup/loyalty/tier_manager.py

import frappe
from frappe.utils import today, date_diff

LOYALTY_PROGRAM = "Dress Up Loyalty Program"
TIER_ORDER = ["Bronze", "Silver", "Gold"]
INACTIVITY_DAYS = 90  # downgrade threshold
WARNING_DAYS = 60  # warning threshold


def update_last_purchase(invoice_doc):
	"""Invoice submit হলে last_purchase_date update + inactivity warning reset।"""
	frappe.db.set_value(
		"Customer",
		invoice_doc.customer,
		{
			"last_purchase_date": invoice_doc.posting_date or today(),
			"inactivity_warned": 0,
		},
	)
	frappe.db.commit()


def run_daily_loyalty_checks():
	"""
	Daily scheduler job।
	সব enrolled customer-এর inactivity check করে।
	60 দিন → warning SMS
	90 দিন → downgrade 1 tier (minimum Bronze)
	"""
	enrolled_customers = frappe.get_all(
		"Customer",
		filters={
			"loyalty_eligible": 1,
			"loyalty_program": LOYALTY_PROGRAM,
		},
		fields=[
			"name",
			"loyalty_program_tier",
			"last_purchase_date",
			"inactivity_warned",
		],
	)

	for c in enrolled_customers:
		if not c.last_purchase_date:
			continue

		days_inactive = date_diff(today(), c.last_purchase_date)

		# 60-day warning (একবারই পাঠাবে)
		if days_inactive >= WARNING_DAYS and not c.inactivity_warned:
			from dressup.dressup.loyalty.notifications import (
				send_inactivity_warning,
			)

			send_inactivity_warning(c.name, days_inactive)
			frappe.db.set_value("Customer", c.name, "inactivity_warned", 1)
			frappe.db.commit()

		# 90-day downgrade
		if days_inactive >= INACTIVITY_DAYS:
			_downgrade_tier(c.name, c.loyalty_program_tier)


def _downgrade_tier(customer_name, current_tier):
	"""
	1 tier নামাবে, minimum Bronze।

	Note: পরবর্তী purchase-এ ERPNext cumulative tier recalculate করবে
	এবং earned tier restore হবে। Downgrade শুধু inactive period-এ effective।
	"""
	if not current_tier or current_tier == "Bronze":
		return

	current_index = (
		TIER_ORDER.index(current_tier) if current_tier in TIER_ORDER else 0
	)
	new_tier = TIER_ORDER[max(current_index - 1, 0)]

	frappe.db.set_value(
		"Customer",
		customer_name,
		{
			"loyalty_program_tier": new_tier,
			"inactivity_warned": 0,
		},
	)
	frappe.db.commit()

	from dressup.dressup.loyalty.notifications import (
		send_tier_downgrade_notification,
	)

	send_tier_downgrade_notification(customer_name, current_tier, new_tier)

	frappe.logger().info(
		f"[Loyalty] {customer_name} downgraded {current_tier} → {new_tier} "
		f"(90-day inactivity)"
	)
