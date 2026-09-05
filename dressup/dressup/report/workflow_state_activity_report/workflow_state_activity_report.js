// Copyright (c) 2026, Prime Technology of Bangladesh and contributors
// For license information, please see license.txt

frappe.query_reports["Workflow State Activity Report"] = {
	filters: [
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: frappe.datetime.month_start(),
			reqd: 1,
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default: frappe.datetime.month_end(),
			reqd: 1,
		},
		{
			fieldname: "user",
			label: __("User"),
			fieldtype: "Link",
			options: "User",
		},
		{
			fieldname: "reference_doctype",
			label: __("DocType"),
			fieldtype: "Link",
			options: "DocType",
			get_query: function () {
				return {
					filters: {
						issingle: 0,
						istable: 0,
					},
				};
			},
		},
		{
			fieldname: "workflow_state",
			label: __("Workflow State"),
			fieldtype: "Link",
			options: "Workflow State",
		},
		{
			fieldname: "group_by",
			label: __("View / Group By"),
			fieldtype: "Select",
			options: [
				"Detailed Logs",
				"Summary by User",
				"Summary by Workflow State",
				"Summary by DocType",
			],
			default: "Detailed Logs",
		},
	],

	formatter: function (value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data, default_formatter);

		if (column.fieldname === "workflow_state" && value) {
			let clean_val = frappe.utils.strip_html(data.workflow_state || "");
			let color = "#3b82f6"; // default blue

			let val_lower = clean_val.lower ? clean_val.lower() : String(clean_val).toLowerCase();
			if (val_lower.includes("approve") || val_lower.includes("complete") || val_lower.includes("pass")) {
				color = "#10b981"; // green
			} else if (val_lower.includes("reject") || val_lower.includes("cancel") || val_lower.includes("fail")) {
				color = "#ef4444"; // red
			} else if (val_lower.includes("audit") || val_lower.includes("review") || val_lower.includes("pending")) {
				color = "#f59e0b"; // amber
			} else if (val_lower.includes("draft")) {
				color = "#6b7280"; // gray
			}

			value = `<span class="indicator-pill" style="background-color: ${color}20; color: ${color}; font-weight: 600; padding: 3px 8px; border-radius: 12px; border: 1px solid ${color}40;">${clean_val}</span>`;
		}

		if (column.fieldname === "previous_state" && value && value !== "-") {
			let clean_val = frappe.utils.strip_html(data.previous_state || "");
			value = `<span style="color: #6b7280; font-style: italic;">${clean_val}</span>`;
		}

		return value;
	},
};
