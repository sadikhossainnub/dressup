# Copyright (c) 2026, Prime Technology of Bangladesh and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import today


class AssetMaintenanceLog(Document):
	def on_submit(self):
		self.create_journal_entry()
		self.update_rented_asset_totals()

	def on_cancel(self):
		self.cancel_journal_entry()
		self.update_rented_asset_totals()

	def create_journal_entry(self):
		"""Create Journal Entry if paid_by is Company"""
		if self.paid_by != "Company":
			return

		if not self.expense_account:
			frappe.throw(_("Please set Expense Account before submitting"))

		if not self.paid_from_account:
			frappe.throw(_("Please set Paid From Account (Cash/Bank) before submitting"))

		je = frappe.new_doc("Journal Entry")
		je.voucher_type = "Journal Entry"
		je.company = self.company
		je.posting_date = self.maintenance_date or today()
		je.user_remark = f"Maintenance: {self.maintenance_type} for {self.asset_name} ({self.rented_asset})"

		# Debit: Maintenance Expense Account
		je.append("accounts", {
			"account": self.expense_account,
			"debit_in_account_currency": self.cost,
			"cost_center": self.cost_center,
		})

		# Credit: Cash/Bank Account
		je.append("accounts", {
			"account": self.paid_from_account,
			"credit_in_account_currency": self.cost,
			"cost_center": self.cost_center,
		})

		je.insert()
		je.submit()

		self.db_set("journal_entry", je.name)

		frappe.msgprint(
			_("Journal Entry {0} created").format(
				frappe.utils.get_link_to_form("Journal Entry", je.name)
			),
			indicator="green",
			alert=True
		)

	def cancel_journal_entry(self):
		"""Cancel linked Journal Entry"""
		if self.journal_entry:
			je = frappe.get_doc("Journal Entry", self.journal_entry)
			if je.docstatus == 1:
				je.cancel()

			self.db_set("journal_entry", "")

	def update_rented_asset_totals(self):
		"""Update Rented Asset's total_maintenance_cost"""
		if self.rented_asset:
			asset = frappe.get_doc("Rented Asset", self.rented_asset)
			asset.update_maintenance_totals()
