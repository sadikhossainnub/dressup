# dressup/dressup/overrides/sales_invoice.py

import frappe
from frappe.utils import flt, cint
from erpnext.accounts.doctype.sales_invoice.sales_invoice import SalesInvoice
from erpnext.accounts.doctype.loyalty_program.loyalty_program import (
	get_loyalty_program_details_with_points,
)

class CustomSalesInvoice(SalesInvoice):
	"""
	Override ERPNext SalesInvoice to customize loyalty tier calculation.
	"""

	def set_loyalty_program_tier(self):
		"""
		Use dynamic tiers from the Loyalty Program.
		"""
		lp_details = get_loyalty_program_details_with_points(
			self.customer,
			company=self.company,
			loyalty_program=self.loyalty_program,
			include_expired_entry=True,
		)
		final_tier = lp_details.tier_name

		if final_tier:
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
