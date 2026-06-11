// Copyright (c) 2026, Prime Technology of Bangladesh and contributors
// For license information, please see license.txt

frappe.query_reports["Work Order Material Availability"] = {
	filters: [
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
		},
		{
			fieldname: "work_order",
			label: __("Work Order"),
			fieldtype: "Link",
			options: "Work Order",
		},
		{
			fieldname: "bom_no",
			label: __("BOM"),
			fieldtype: "Link",
			options: "BOM",
		},
		{
			fieldname: "bom_type",
			label: __("BOM Type"),
			fieldtype: "Select",
			options: "\nTemplate\nDefault",
		},
		{
			fieldname: "bom_variant",
			label: __("BOM Variant"),
			fieldtype: "Select",
			options: "\nSample Making\nBulk Production",
		},
		{
			fieldname: "item_code",
			label: __("Item Code (Raw Material)"),
			fieldtype: "Link",
			options: "Item",
		},
		{
			fieldname: "status",
			label: __("Status"),
			fieldtype: "Select",
			options: "\nNot Started\nIn Progress\nCompleted\nStopped\nDraft",
		},
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
		},
	],
};
