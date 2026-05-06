import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def execute():
	custom_fields = {
		"BOM": [
			{
				"fieldname": "custom_tech_pack_no",
				"label": "Tech Pack No",
				"fieldtype": "Link",
				"options": "Sketch Specification Sample Making Sheet",
				"insert_after": "item",
				"read_only": 1
			},
			{
				"fieldname": "pre_production_sample",
				"label": "Pre Production Sample",
				"fieldtype": "Link",
				"options": "Pre Production Sample",
				"insert_after": "custom_tech_pack_no",
				"read_only": 1
			},
			{
				"fieldname": "bom_type",
				"label": "BOM Type",
				"fieldtype": "Select",
				"options": "\nSample Making\nBulk Production",
				"insert_after": "pre_production_sample"
			}
		],
		"Work Order": [
			{
				"fieldname": "custom_tech_pack_no",
				"label": "Tech Pack No",
				"fieldtype": "Link",
				"options": "Sketch Specification Sample Making Sheet",
				"insert_after": "production_item",
				"read_only": 1
			},
			{
				"fieldname": "pre_production_sample",
				"label": "Pre Production Sample",
				"fieldtype": "Link",
				"options": "Pre Production Sample",
				"insert_after": "custom_tech_pack_no",
				"read_only": 1
			}
		]
	}

	create_custom_fields(custom_fields, ignore_validate=True)
	
	# Export the custom fields to fixtures
	frappe.call("frappe.utils.fixtures.export_fixtures")
	print("Custom fields added and fixtures exported")
