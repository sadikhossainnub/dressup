// Copyright (c) 2026, Prime Technology of Bangladesh and contributors
// For license information, please see license.txt

frappe.query_reports["Loyalty Program Summary Report"] = {
	filters: [
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
			reqd: 1,
		},
		{
			fieldname: "loyalty_program",
			label: __("Loyalty Program"),
			fieldtype: "Link",
			options: "Loyalty Program",
		},
		{
			fieldname: "tier",
			label: __("Current Tier"),
			fieldtype: "Data",
		},
		{
			fieldname: "expiry_warning_days",
			label: __("Expiry Warning Threshold (Days)"),
			fieldtype: "Int",
			default: 7,
		},
	],
};

