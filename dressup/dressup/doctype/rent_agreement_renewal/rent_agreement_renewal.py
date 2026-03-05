# Copyright (c) 2026, Prime Technology of Bangladesh and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, flt


class RentAgreementRenewal(Document):
	def validate(self):
		self.validate_dates()
		self.calculate_rent_change()

	def validate_dates(self):
		if self.new_start_date and self.new_end_date:
			if getdate(self.new_end_date) <= getdate(self.new_start_date):
				frappe.throw(_("New End Date must be after New Start Date"))

	def calculate_rent_change(self):
		"""Calculate rent change percentage"""
		if self.previous_rent and self.previous_rent > 0 and self.new_monthly_rent:
			self.rent_change_percentage = flt(
				((self.new_monthly_rent - self.previous_rent) / self.previous_rent) * 100, 2
			)
		else:
			self.rent_change_percentage = 0

	def on_submit(self):
		self.update_rented_asset()

	def on_cancel(self):
		self.revert_rented_asset()

	def update_rented_asset(self):
		"""Update Rented Asset with new agreement details"""
		asset = frappe.get_doc("Rented Asset", self.rented_asset)

		asset.agreement_start_date = self.new_start_date
		asset.agreement_end_date = self.new_end_date
		asset.monthly_rent = self.new_monthly_rent

		if self.new_advance_amount:
			asset.security_deposit = self.new_advance_amount

		asset.status = "Active"
		asset.save()

		frappe.msgprint(
			_("Rented Asset {0} updated with new agreement details").format(
				frappe.utils.get_link_to_form("Rented Asset", self.rented_asset)
			),
			indicator="green",
			alert=True
		)

	def revert_rented_asset(self):
		"""Revert Rented Asset to previous agreement details"""
		asset = frappe.get_doc("Rented Asset", self.rented_asset)

		asset.agreement_start_date = self.previous_start_date
		asset.agreement_end_date = self.previous_end_date
		asset.monthly_rent = self.previous_rent
		asset.save()

		frappe.msgprint(
			_("Rented Asset {0} reverted to previous agreement details").format(
				frappe.utils.get_link_to_form("Rented Asset", self.rented_asset)
			),
			indicator="orange",
			alert=True
		)
