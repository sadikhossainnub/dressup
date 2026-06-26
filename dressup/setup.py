# Copyright (c) 2026, Prime Technology of Bangladesh and contributors
# For license information, please see license.txt

import frappe


def after_install():
	add_net_qty_to_shipping_rule()
	create_work_order_report()
	add_show_created_by_custom_field()


def after_migrate():
	add_net_qty_to_shipping_rule()
	create_work_order_report()
	add_show_created_by_custom_field()


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
