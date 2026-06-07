# Copyright (c) 2026, Prime Technology of Bangladesh and contributors
# For license information, please see license.txt

"""
Shipping Rule: Net Qty Support
================================

ERPNext's Shipping Rule only supports "Fixed", "Net Total", and "Net Weight"
for the Calculate Based On field. This module adds "Net Qty" support by
overriding the ShippingRule class.

When "Net Qty" is selected, the shipping amount is calculated based on the
total quantity of items in the transaction (doc.total_qty).
"""

import frappe
from frappe import _
from frappe.utils import flt

from erpnext.accounts.doctype.shipping_rule.shipping_rule import ShippingRule


class CustomShippingRule(ShippingRule):
	def apply(self, doc):
		"""Apply shipping rule on given doc. Extends base to support Net Qty."""

		shipping_amount = 0.0
		by_value = False
		multiply_by_qty = False

		if doc.get_shipping_address():
			self.validate_countries(doc)

		if self.calculate_based_on == "Net Total":
			value = doc.base_net_total
			by_value = True

		elif self.calculate_based_on == "Net Weight":
			value = doc.total_net_weight
			by_value = True

		elif self.calculate_based_on in ("Net Qty", "Net Qty (Flat)"):
			value = flt(doc.total_qty)
			by_value = True

		elif self.calculate_based_on == "Net Qty (Per Qty)":
			value = flt(doc.total_qty)
			by_value = True
			multiply_by_qty = True

		elif self.calculate_based_on == "Fixed":
			shipping_amount = self.shipping_amount

		if by_value:
			shipping_amount = self.get_shipping_amount_from_rules(value)
			if multiply_by_qty:
				shipping_amount = flt(shipping_amount * value)

		# convert to order currency
		if doc.currency != doc.company_currency:
			shipping_amount = flt(shipping_amount / doc.conversion_rate, 2)

		self.add_shipping_rule_to_tax_table(doc, shipping_amount)
