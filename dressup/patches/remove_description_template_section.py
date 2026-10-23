# Copyright (c) 2026, Prime Technology of Bangladesh and contributors
# For license information, please see license.txt

"""
Patch: Remove 'Item-description_template_section' Section Break custom field from Item.
The Description Template link field now sits directly after 'brand' without a section wrapper.
"""

import frappe


def execute():
	cf_name = "Item-description_template_section"
	if frappe.db.exists("Custom Field", cf_name):
		frappe.delete_doc("Custom Field", cf_name, ignore_permissions=True)
		frappe.clear_cache(doctype="Item")
		frappe.db.commit()

	# Also fix insert_after for description_template to point directly to brand
	if frappe.db.exists("Custom Field", "Item-description_template"):
		frappe.db.set_value("Custom Field", "Item-description_template", "insert_after", "brand")
		frappe.clear_cache(doctype="Item")
		frappe.db.commit()

