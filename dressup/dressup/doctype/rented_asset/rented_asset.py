# Copyright (c) 2026, Prime Technology of Bangladesh and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, today


class RentedAsset(Document):
	def validate(self):
		self.validate_dates()

	def validate_dates(self):
		if self.agreement_start_date and self.agreement_end_date:
			if getdate(self.agreement_end_date) <= getdate(self.agreement_start_date):
				frappe.throw(_("Agreement End Date must be after Agreement Start Date"))

		# Auto-expire status
		if self.agreement_end_date and getdate(self.agreement_end_date) < getdate(today()):
			if self.status == "Active":
				self.status = "Expired"

	def update_payment_totals(self):
		"""Calculate total_paid from Payment Entries linked to Supplier for this asset"""
		total_paid = frappe.db.sql("""
			SELECT IFNULL(SUM(pe.paid_amount), 0)
			FROM `tabPayment Entry` pe
			WHERE pe.party_type = 'Supplier'
			AND pe.party = %s
			AND pe.docstatus = 1
			AND pe.payment_type = 'Pay'
			AND pe.custom_rented_asset = %s
		""", (self.supplier, self.name))[0][0] or 0

		self.db_set("total_paid", total_paid, update_modified=False)

	def update_maintenance_totals(self):
		"""Calculate total_maintenance_cost from Asset Maintenance Logs"""
		total_cost = frappe.db.sql("""
			SELECT IFNULL(SUM(cost), 0)
			FROM `tabAsset Maintenance Log`
			WHERE rented_asset = %s
			AND docstatus = 1
			AND paid_by = 'Company'
		""", self.name)[0][0] or 0

		self.db_set("total_maintenance_cost", total_cost, update_modified=False)

	@frappe.whitelist()
	def make_rent_payment(self):
		"""Create ERPNext Payment Entry pre-filled with rent details"""
		if not self.supplier:
			frappe.throw(_("Please set a Supplier (Owner/Landlord) first"))

		pe = frappe.new_doc("Payment Entry")
		pe.payment_type = "Pay"
		pe.party_type = "Supplier"
		pe.party = self.supplier
		pe.party_name = self.supplier_name
		pe.company = self.company
		pe.paid_amount = self.monthly_rent
		pe.received_amount = self.monthly_rent
		pe.custom_rented_asset = self.name
		pe.cost_center = self.default_cost_center

		if self.default_mode_of_payment:
			pe.mode_of_payment = self.default_mode_of_payment

		pe.reference_no = f"Rent-{self.name}"
		pe.reference_date = today()

		return pe

	@frappe.whitelist()
	def pay_deposit(self):
		"""Create Journal Entry for security deposit payment"""
		if self.deposit_paid:
			frappe.throw(_("Deposit has already been paid"))

		if not self.security_deposit or self.security_deposit <= 0:
			frappe.throw(_("Security Deposit amount must be greater than 0"))

		if not self.security_deposit_account:
			frappe.throw(_("Please set Security Deposit Account in Accounting Defaults"))

		# Get default bank/cash account
		default_account = frappe.db.get_value(
			"Mode of Payment Account",
			{"parent": self.default_mode_of_payment, "company": self.company},
			"default_account"
		) if self.default_mode_of_payment else None

		if not default_account:
			frappe.throw(_("Please set Default Mode of Payment with a default account"))

		je = frappe.new_doc("Journal Entry")
		je.voucher_type = "Journal Entry"
		je.company = self.company
		je.posting_date = today()
		je.user_remark = f"Security Deposit for {self.asset_name} ({self.name})"

		# Debit: Security Deposit Account (Asset)
		je.append("accounts", {
			"account": self.security_deposit_account,
			"debit_in_account_currency": self.security_deposit,
			"cost_center": self.default_cost_center,
			"party_type": "Supplier",
			"party": self.supplier,
		})

		# Credit: Cash/Bank Account
		je.append("accounts", {
			"account": default_account,
			"credit_in_account_currency": self.security_deposit,
			"cost_center": self.default_cost_center,
		})

		je.insert()
		je.submit()

		self.db_set("deposit_paid", 1)
		self.db_set("deposit_journal_entry", je.name)

		frappe.msgprint(
			_("Security Deposit Journal Entry {0} created successfully").format(
				frappe.utils.get_link_to_form("Journal Entry", je.name)
			),
			indicator="green",
			alert=True
		)

		return je.name

	@frappe.whitelist()
	def refund_deposit(self):
		"""Create reverse Journal Entry for deposit refund"""
		if not self.deposit_paid:
			frappe.throw(_("Deposit has not been paid yet"))

		if self.deposit_refunded:
			frappe.throw(_("Deposit has already been refunded"))

		if not self.security_deposit_account:
			frappe.throw(_("Please set Security Deposit Account"))

		default_account = frappe.db.get_value(
			"Mode of Payment Account",
			{"parent": self.default_mode_of_payment, "company": self.company},
			"default_account"
		) if self.default_mode_of_payment else None

		if not default_account:
			frappe.throw(_("Please set Default Mode of Payment with a default account"))

		je = frappe.new_doc("Journal Entry")
		je.voucher_type = "Journal Entry"
		je.company = self.company
		je.posting_date = today()
		je.user_remark = f"Security Deposit Refund for {self.asset_name} ({self.name})"

		# Debit: Cash/Bank Account (receiving money back)
		je.append("accounts", {
			"account": default_account,
			"debit_in_account_currency": self.security_deposit,
			"cost_center": self.default_cost_center,
		})

		# Credit: Security Deposit Account (reducing asset)
		je.append("accounts", {
			"account": self.security_deposit_account,
			"credit_in_account_currency": self.security_deposit,
			"cost_center": self.default_cost_center,
			"party_type": "Supplier",
			"party": self.supplier,
		})

		je.insert()
		je.submit()

		self.db_set("deposit_refunded", 1)
		self.db_set("refund_journal_entry", je.name)

		frappe.msgprint(
			_("Deposit Refund Journal Entry {0} created successfully").format(
				frappe.utils.get_link_to_form("Journal Entry", je.name)
			),
			indicator="green",
			alert=True
		)

		return je.name
