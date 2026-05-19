# dressup/dressup/overrides/sales_invoice.py

import frappe
from frappe.utils import flt, cint
from erpnext.accounts.doctype.sales_invoice.sales_invoice import SalesInvoice
from erpnext.accounts.doctype.loyalty_program.loyalty_program import (
	get_loyalty_program_details_with_points,
)

TIER_ORDER = ["Bronze", "Silver", "Gold"]
SINGLE_TXN_UPGRADE_AMOUNT = 100000  # ৳1,00,000


class CustomSalesInvoice(SalesInvoice):
	"""
	Override ERPNext SalesInvoice to customize loyalty tier calculation.

	ERPNext's native set_loyalty_program_tier() recalculates tier purely
	from cumulative spend on every invoice submit. This override adds:
	  - Single-txn ≥ ৳1L instant upgrade (bump 1 tier above cumulative)
	"""

	def set_loyalty_program_tier(self):
		"""
		1. Calculate ERPNext's cumulative tier (same logic as original)
		2. If this invoice ≥ ৳1L, bump 1 tier above cumulative
		3. Set the HIGHER of the two
		"""
		lp_details = get_loyalty_program_details_with_points(
			self.customer,
			company=self.company,
			loyalty_program=self.loyalty_program,
			include_expired_entry=True,
		)
		cumulative_tier = lp_details.tier_name or "Bronze"
		final_tier = cumulative_tier

		# Single-txn upgrade check
		if flt(self.grand_total) >= SINGLE_TXN_UPGRADE_AMOUNT:
			cum_idx = TIER_ORDER.index(cumulative_tier) if cumulative_tier in TIER_ORDER else 0
			upgraded_idx = min(cum_idx + 1, len(TIER_ORDER) - 1)
			upgraded_tier = TIER_ORDER[upgraded_idx]

			if upgraded_idx > cum_idx:
				final_tier = upgraded_tier

				from dressup.dressup.loyalty.notifications import (
					send_tier_upgrade_notification,
				)
				send_tier_upgrade_notification(
					self.customer, cumulative_tier, final_tier
				)
				frappe.logger().info(
					f"[Loyalty] {self.customer} upgraded {cumulative_tier} → {final_tier} "
					f"(single txn ৳{self.grand_total})"
				)

		frappe.db.set_value(
			"Customer", self.customer, "loyalty_program_tier", final_tier
		)


# ─── doc_events hooks (run AFTER the class methods) ───


def on_submit(doc, method):
	"""Sales Invoice submit হলে loyalty housekeeping।"""
	if not doc.customer:
		return

	from dressup.dressup.loyalty.tier_manager import update_last_purchase
	from dressup.dressup.loyalty.eligibility import check_eligibility_on_invoice

	# Step 1: last_purchase_date update + inactivity warn reset
	update_last_purchase(doc)

	# Step 2: Eligibility check (enroll if ৳10k/month threshold met)
	check_eligibility_on_invoice(doc)


def on_cancel(doc, method):
	"""
	Invoice cancel হলে — ERPNext নিজেই Loyalty Point Entry reverse করে।
	আমাদের extra কিছু করার নেই।
	"""
	pass
