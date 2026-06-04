# Copyright (c) 2026, Prime Technology of Bangladesh and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, flt


class LoyaltyDowngradeSettings(Document):

	def validate(self):
		if self.enabled:
			if not self.loyalty_program:
				frappe.throw(_("Please select a Loyalty Program before enabling downgrade."))
			if not self.company:
				frappe.throw(_("Please select a Company before enabling downgrade."))

			# Validate the loyalty program is a Multiple Tier Program
			lp_type = frappe.db.get_value("Loyalty Program", self.loyalty_program, "loyalty_program_type")
			if lp_type != "Multiple Tier Program":
				frappe.throw(
					_("Loyalty Program <b>{0}</b> must be a <b>Multiple Tier Program</b> for downgrade to work.").format(
						self.loyalty_program
					)
				)

		if self.enable_period_downgrade:
			if not self.evaluation_period:
				frappe.throw(_("Please select an Evaluation Period for period-based downgrade."))
			if flt(self.maintain_amount) <= 0:
				frappe.throw(_("Minimum Maintain Amount must be greater than 0."))
			if not self.period_downgrade_type:
				frappe.throw(_("Please select a Downgrade Type for period-based downgrade."))

		if self.enable_inactivity_downgrade:
			if cint(self.inactive_days) <= 0:
				frappe.throw(_("Inactive Days Threshold must be greater than 0."))
			if not self.inactivity_downgrade_type:
				frappe.throw(_("Please select a Downgrade Type for inactivity-based downgrade."))
