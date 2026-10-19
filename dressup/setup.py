# Copyright (c) 2026, Prime Technology of Bangladesh and contributors
# For license information, please see license.txt

import frappe


def after_install():
	add_net_qty_to_shipping_rule()
	create_work_order_report()
	create_customer_ledger_report()
	add_show_created_by_custom_field()
	add_tier_enable_amount_custom_field()
	add_yearly_upgrade_amount_custom_field()
	create_loyalty_program_summary_report()
	create_loyalty_tier_upgrade_settings()


def after_migrate():
	add_net_qty_to_shipping_rule()
	create_work_order_report()
	create_customer_ledger_report()
	add_show_created_by_custom_field()
	add_tier_enable_amount_custom_field()
	add_yearly_upgrade_amount_custom_field()
	create_loyalty_program_summary_report()
	create_loyalty_tier_upgrade_settings()


def create_work_order_report():
	if not frappe.db.exists("Report", "Work Order Material Availability"):
		report = frappe.get_doc({
			"doctype": "Report",
			"report_name": "Work Order Material Availability",
			"ref_doctype": "Work Order",
			"report_type": "Script Report",
			"is_standard": "Yes",
			"module": "DressUp",
		})
		report.flags.ignore_permissions = True
		report.insert()
		frappe.db.commit()


def create_customer_ledger_report():
	if not frappe.db.exists("Report", "Customer Ledger Report"):
		report = frappe.get_doc({
			"doctype": "Report",
			"report_name": "Customer Ledger Report",
			"ref_doctype": "Customer",
			"report_type": "Script Report",
			"is_standard": "Yes",
			"module": "DressUp",
		})
		report.flags.ignore_permissions = True
		report.insert()
		frappe.db.commit()


def add_net_qty_to_shipping_rule():
	"""Add 'Net Qty (Flat)' and 'Net Qty (Per Qty)' options to Shipping Rule's Calculate Based On field."""
	# Define target options
	target_options = "Fixed\nNet Total\nNet Weight\nNet Qty (Flat)\nNet Qty (Per Qty)"

	# Use Property Setter to set the options without modifying core
	property_setter_filters = {
		"doc_type": "Shipping Rule",
		"field_name": "calculate_based_on",
		"property": "options",
		"module": "DressUp",
	}

	if frappe.db.exists("Property Setter", property_setter_filters):
		frappe.db.set_value(
			"Property Setter",
			property_setter_filters,
			"value",
			target_options,
		)
	else:
		ps = frappe.get_doc({
			"doctype": "Property Setter",
			"doctype_or_field": "DocField",
			"doc_type": "Shipping Rule",
			"field_name": "calculate_based_on",
			"property": "options",
			"value": target_options,
			"property_type": "Small Text",
			"module": "DressUp",
		})
		ps.flags.ignore_permissions = True
		ps.insert()

	frappe.clear_cache(doctype="Shipping Rule")
	frappe.db.commit()


def add_show_created_by_custom_field():
	if not frappe.db.exists("Custom Field", {"dt": "List View Settings", "fieldname": "show_created_by"}):
		cf = frappe.get_doc({
			"doctype": "Custom Field",
			"dt": "List View Settings",
			"fieldname": "show_created_by",
			"label": "Show Created By",
			"fieldtype": "Check",
			"insert_after": "disable_automatic_recency_filters",
			"default": "0",
			"module": "DressUp"
		})
		cf.flags.ignore_permissions = True
		cf.insert()
		frappe.db.commit()
		frappe.clear_cache(doctype="List View Settings")


def add_tier_enable_amount_custom_field():
	if not frappe.db.exists("Custom Field", {"dt": "Loyalty Program Collection", "fieldname": "tier_enable_amount"}):
		cf = frappe.get_doc({
			"doctype": "Custom Field",
			"dt": "Loyalty Program Collection",
			"fieldname": "tier_enable_amount",
			"label": "Tier Enable Amount (Check Point)",
			"fieldtype": "Currency",
			"insert_after": "min_spent",
			"description": "Minimum total spend in current month (1st to 30th/31st) to activate this Tier.",
			"module": "DressUp"
		})
		cf.flags.ignore_permissions = True
		cf.insert()
		frappe.db.commit()
		frappe.clear_cache(doctype="Loyalty Program Collection")


def add_yearly_upgrade_amount_custom_field():
	"""
	Loyalty Program Collection-এ 'yearly_upgrade_amount' কাস্টম ফিল্ড যোগ করে।
	এই ফিল্ডে মান দিলে Rolling 12 months-এর মোট খরচ যাচাই করে Tier আপগ্রেড হবে।
	১ম Tier-এর জন্য ০ রাখুন — সেটি tier_enable_amount দিয়ে মাসিক চেক হবে।
	"""
	if not frappe.db.exists("Custom Field", {"dt": "Loyalty Program Collection", "fieldname": "yearly_upgrade_amount"}):
		cf = frappe.get_doc({
			"doctype": "Custom Field",
			"dt": "Loyalty Program Collection",
			"fieldname": "yearly_upgrade_amount",
			"label": "Yearly Upgrade Amount",
			"fieldtype": "Currency",
			"insert_after": "tier_enable_amount",
			"description": (
				"Rolling 12 months-এ মোট কত টাকা কিনলে এই Tier-এ আপগ্রেড হবে। "
				"১ম Tier-এর জন্য ০ রাখুন (সেটি Tier Enable Amount দিয়ে চলবে)।"
			),
			"module": "DressUp"
		})
		cf.flags.ignore_permissions = True
		cf.insert()
		frappe.db.commit()
		frappe.clear_cache(doctype="Loyalty Program Collection")


def create_loyalty_program_summary_report():
	"""Loyalty Program Summary Report তৈরি করে যদি না থাকে।"""
	if not frappe.db.exists("Report", "Loyalty Program Summary Report"):
		report = frappe.get_doc({
			"doctype": "Report",
			"report_name": "Loyalty Program Summary Report",
			"ref_doctype": "Customer",
			"report_type": "Script Report",
			"is_standard": "Yes",
			"module": "DressUp",
		})
		report.flags.ignore_permissions = True
		report.insert()
		frappe.db.commit()


def create_loyalty_tier_upgrade_settings():
	"""Loyalty Tier Upgrade Settings Single DocType-এ ডিফল্ট রেকর্ড তৈরি করে।"""
	if not frappe.db.exists("Loyalty Tier Upgrade Settings", "Loyalty Tier Upgrade Settings"):
		doc = frappe.new_doc("Loyalty Tier Upgrade Settings")
		doc.flags.ignore_permissions = True
		doc.insert()
		frappe.db.commit()
