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
	add_item_description_template_custom_fields()
	create_default_item_description_template()


def after_migrate():
	add_net_qty_to_shipping_rule()
	create_work_order_report()
	create_customer_ledger_report()
	add_show_created_by_custom_field()
	add_tier_enable_amount_custom_field()
	add_yearly_upgrade_amount_custom_field()
	create_loyalty_program_summary_report()
	create_loyalty_tier_upgrade_settings()
	add_item_description_template_custom_fields()
	create_default_item_description_template()


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


def add_item_description_template_custom_fields():
	"""Add custom fields on Item for Item Description Template."""
	custom_fields = [
		{
			"dt": "Item",
			"fieldname": "description_template",
			"label": "Description Template",
			"fieldtype": "Link",
			"options": "Item Description Template",
			"link_filters": '[["Item Description Template", "enabled", "=", 1]]',
			"insert_after": "brand",
			"module": "DressUp",
		},
		{
			"dt": "Item",
			"fieldname": "regenerate_description",
			"label": "Regenerate description on save",
			"fieldtype": "Check",
			"default": "1",
			"insert_after": "description_template",
			"module": "DressUp",
		},
		{
			"dt": "Item",
			"fieldname": "description_values",
			"label": "Description Values",
			"fieldtype": "Table",
			"options": "Item Description Value",
			"insert_after": "regenerate_description",
			"module": "DressUp",
		},
	]

	for field_def in custom_fields:
		cf_name = f"{field_def['dt']}-{field_def['fieldname']}"
		if frappe.db.exists("Custom Field", cf_name):
			frappe.db.set_value("Custom Field", cf_name, "insert_after", field_def["insert_after"])
		elif not frappe.db.exists("Custom Field", {"dt": field_def["dt"], "fieldname": field_def["fieldname"]}):
			cf = frappe.get_doc({
				"doctype": "Custom Field",
				**field_def,
			})
			cf.flags.ignore_permissions = True
			cf.insert()

	frappe.clear_cache(doctype="Item")
	frappe.db.commit()


DEFAULT_TEMPLATE_HTML = """<div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size: 13px; line-height: 1.5; color: #1e293b;">

<div style="text-align: center; margin-bottom: 12px;">
<span style="display: inline-block; font-size: 11px; font-weight: 600; color: #475569; background-color: #f1f5f9; padding: 4px 10px; border-radius: 4px; border: 1px solid #e2e8f0;">
Expected deviation +/- {{ deviation or "0.5" }} inch.
</span>
</div>

<h4 style="margin: 0 0 4px 0; color: #0f172a; font-size: 15px; font-weight: bold; text-align: left;">
Size Chart{% if size_title %} — {{ size_title }}{% endif %}{% if item_code %} ({{ item_code }}){% endif %}
</h4>

{% if size_type or size_fabric or size_value_addition %}
<p style="margin: 0 0 14px 0; font-size: 12px; color: #64748b; line-height: 1.4; text-align: left;">
{% if size_type %}<strong>Type:</strong> {{ size_type }}{% endif %}{% if size_fabric %}{% if size_type %} | {% endif %}<strong>Fabric:</strong> {{ size_fabric }}{% endif %}{% if size_value_addition %}{% if size_type or size_fabric %} | {% endif %}<strong>Value Addition:</strong> {{ size_value_addition }}{% endif %}
</p>
{% endif %}

{% if kameez_body or kameez_length or kameez_sleeve %}
<h4 style="margin: 12px 0 6px 0; color: #0f172a; font-size: 12px; font-weight: bold; text-transform: uppercase; letter-spacing: 0.5px;">Kameez / Top Fabric Measurements</h4>
<table border="1" cellpadding="8" cellspacing="0" style="width: 100%; border-collapse: collapse; text-align: center; font-size: 12px; border: 1px solid #cbd5e1; margin-bottom: 16px;">
<tbody>
<tr style="background-color: #f8fafc; color: #0f172a;">
<td style="padding: 7px 4px; width: 34%; border: 1px solid #cbd5e1; font-size: 11px; font-weight: bold; text-transform: uppercase; text-align: center; background-color: #f8fafc;"><strong>BODY</strong></td>
<td style="padding: 7px 4px; width: 33%; border: 1px solid #cbd5e1; font-size: 11px; font-weight: bold; text-transform: uppercase; text-align: center; background-color: #f8fafc;"><strong>LENGTH</strong></td>
<td style="padding: 7px 4px; width: 33%; border: 1px solid #cbd5e1; font-size: 11px; font-weight: bold; text-transform: uppercase; text-align: center; background-color: #f8fafc;"><strong>SLEEVE</strong></td>
</tr>
<tr>
<td style="padding: 8px 4px; border: 1px solid #cbd5e1; text-align: center;">{{ kameez_body }}{% if kameez_body and not kameez_body.endswith('"') %}"{% endif %}</td>
<td style="padding: 8px 4px; border: 1px solid #cbd5e1; text-align: center;">{{ kameez_length }}{% if kameez_length and not kameez_length.endswith('"') %}"{% endif %}</td>
<td style="padding: 8px 4px; border: 1px solid #cbd5e1; text-align: center;">{{ kameez_sleeve }}{% if kameez_sleeve and not kameez_sleeve.endswith('"') %}"{% endif %}</td>
</tr>
</tbody>
</table>
{% endif %}

{% if salwar_length or salwar_width %}
<h4 style="margin: 12px 0 6px 0; color: #0f172a; font-size: 12px; font-weight: bold; text-transform: uppercase; letter-spacing: 0.5px;">Salwar / Bottom Fabric Measurements</h4>
<table border="1" cellpadding="8" cellspacing="0" style="width: 100%; border-collapse: collapse; text-align: center; font-size: 12px; border: 1px solid #cbd5e1; margin-bottom: 16px;">
<tbody>
<tr style="background-color: #f8fafc; color: #0f172a;">
<td style="padding: 7px 4px; width: 50%; border: 1px solid #cbd5e1; font-size: 11px; font-weight: bold; text-transform: uppercase; text-align: center; background-color: #f8fafc;"><strong>LENGTH</strong></td>
<td style="padding: 7px 4px; width: 50%; border: 1px solid #cbd5e1; font-size: 11px; font-weight: bold; text-transform: uppercase; text-align: center; background-color: #f8fafc;"><strong>WIDTH</strong></td>
</tr>
<tr>
<td style="padding: 8px 4px; border: 1px solid #cbd5e1; text-align: center;">{{ salwar_length }}{% if salwar_length and not salwar_length.endswith('"') %}"{% endif %}{% if (salwar_length | float) > 0 %} ({{ (salwar_length | float / 36) | round(2) }} Yds){% endif %}</td>
<td style="padding: 8px 4px; border: 1px solid #cbd5e1; text-align: center;">{{ salwar_width }}{% if salwar_width and not salwar_width.endswith('"') %}"{% endif %}{% if (salwar_width | float) > 0 %} ({{ (salwar_width | float / 36) | round(2) }} Yds){% endif %}</td>
</tr>
</tbody>
</table>
{% endif %}

{% if dupatta_length or dupatta_width %}
<h4 style="margin: 12px 0 6px 0; color: #0f172a; font-size: 12px; font-weight: bold; text-transform: uppercase; letter-spacing: 0.5px;">Dupatta Measurements</h4>
<table border="1" cellpadding="8" cellspacing="0" style="width: 100%; border-collapse: collapse; text-align: center; font-size: 12px; border: 1px solid #cbd5e1; margin-bottom: 16px;">
<tbody>
<tr style="background-color: #f8fafc; color: #0f172a;">
<td style="padding: 7px 4px; width: 50%; border: 1px solid #cbd5e1; font-size: 11px; font-weight: bold; text-transform: uppercase; text-align: center; background-color: #f8fafc;"><strong>LENGTH</strong></td>
<td style="padding: 7px 4px; width: 50%; border: 1px solid #cbd5e1; font-size: 11px; font-weight: bold; text-transform: uppercase; text-align: center; background-color: #f8fafc;"><strong>WIDTH</strong></td>
</tr>
<tr>
<td style="padding: 8px 4px; border: 1px solid #cbd5e1; text-align: center;">{{ dupatta_length }}{% if dupatta_length and not dupatta_length.endswith('"') %}"{% endif %}</td>
<td style="padding: 8px 4px; border: 1px solid #cbd5e1; text-align: center;">{{ dupatta_width }}{% if dupatta_width and not dupatta_width.endswith('"') %}"{% endif %}</td>
</tr>
</tbody>
</table>
{% endif %}

<small style="color: #64748b; display: block; margin-top: 8px; font-size: 11px;">* All measurements are in inches unless otherwise stated.</small>
</div>"""


def create_default_item_description_template():
	"""Seed the default 'Unstitched Three Piece' template if it does not already exist."""
	template_name = "Unstitched Three Piece"
	if frappe.db.exists("Item Description Template", template_name):
		return

	fields = [
		{"field_key": "size_title", "field_label": "Size Title", "default_value": ""},
		{"field_key": "size_type", "field_label": "Size Type", "default_value": ""},
		{"field_key": "size_fabric", "field_label": "Size Fabric", "default_value": ""},
		{"field_key": "size_value_addition", "field_label": "Size Value Addition", "default_value": ""},
		{"field_key": "deviation", "field_label": "Deviation", "default_value": "0.5"},
		{"field_key": "kameez_body", "field_label": "Kameez Body", "default_value": ""},
		{"field_key": "kameez_length", "field_label": "Kameez Length", "default_value": ""},
		{"field_key": "kameez_sleeve", "field_label": "Kameez Sleeve", "default_value": ""},
		{"field_key": "salwar_length", "field_label": "Salwar Length", "default_value": ""},
		{"field_key": "salwar_width", "field_label": "Salwar Width", "default_value": ""},
		{"field_key": "dupatta_length", "field_label": "Dupatta Length", "default_value": ""},
		{"field_key": "dupatta_width", "field_label": "Dupatta Width", "default_value": ""},
	]

	doc = frappe.get_doc({
		"doctype": "Item Description Template",
		"template_name": template_name,
		"enabled": 1,
		"update_web_description": 1,
		"template_html": DEFAULT_TEMPLATE_HTML,
		"fields": fields,
	})
	doc.flags.ignore_permissions = True
	doc.insert()
	frappe.db.commit()

