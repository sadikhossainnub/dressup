# Copyright (c) 2026, Prime Technology of Bangladesh and contributors
# For license information, please see license.txt

import frappe


def after_install():
	add_net_qty_to_shipping_rule()


def after_migrate():
	add_net_qty_to_shipping_rule()


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
