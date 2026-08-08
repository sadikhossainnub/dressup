// Copyright (c) 2026, Prime Technology of Bangladesh and contributors
// For license information, please see license.txt

frappe.query_reports["Sales Order Master Report"] = {
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
			fieldname: "sales_order",
			label: __("Sales Order"),
			fieldtype: "Link",
			options: "Sales Order",
		},
		{
			fieldname: "customer",
			label: __("Customer"),
			fieldtype: "Link",
			options: "Customer",
		},
		{
			fieldname: "customer_group",
			label: __("Customer Group"),
			fieldtype: "Link",
			options: "Customer Group",
		},
		{
			fieldname: "territory",
			label: __("Territory"),
			fieldtype: "Link",
			options: "Territory",
		},
		{
			fieldname: "status",
			label: __("Status"),
			fieldtype: "Select",
			options: "\nDraft\nOn Hold\nTo Deliver and Bill\nTo Bill\nTo Deliver\nCompleted\nCancelled\nClosed",
		},
		{
			fieldname: "created_by",
			label: __("Created By"),
			fieldtype: "Link",
			options: "User",
		},
		{
			fieldname: "sales_person",
			label: __("Sales Person"),
			fieldtype: "Link",
			options: "Sales Person",
		},
		{
			fieldname: "item_code",
			label: __("Item Code"),
			fieldtype: "Link",
			options: "Item",
		},
		{
			fieldname: "approval_status",
			label: __("Approval Status"),
			fieldtype: "Select",
			options: "\nPending\nApproved\nRejected",
		},
	],

	formatter: function (value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data, default_formatter);

		if (column.fieldname === "status") {
			const color_map = {
				"Draft":                 "#6b7280",
				"On Hold":              "#d97706",
				"To Deliver and Bill":  "#2563eb",
				"To Bill":              "#7c3aed",
				"To Deliver":           "#0891b2",
				"Completed":            "#059669",
				"Cancelled":            "#dc2626",
				"Closed":               "#374151",
			};
			const clr = color_map[data && data.status] || "#6b7280";
			value = `<span style="color:${clr}; font-weight:600;">${value}</span>`;
		}

		if (column.fieldname === "approval_status") {
			const color_map = {
				"Pending":  "#d97706",
				"Approved": "#059669",
				"Rejected": "#dc2626",
			};
			const clr = color_map[data && data.approval_status] || "#6b7280";
			if (data && data.approval_status) {
				value = `<span style="color:${clr}; font-weight:600;">${value}</span>`;
			}
		}

		if (column.fieldname === "delivery_status") {
			const color_map = {
				"Not Delivered":       "#dc2626",
				"Partially Delivered": "#d97706",
				"Fully Delivered":     "#059669",
			};
			const clr = color_map[data && data.delivery_status] || "#6b7280";
			if (data && data.delivery_status) {
				value = `<span style="color:${clr}; font-weight:600;">${value}</span>`;
			}
		}

		if (column.fieldname === "per_delivered") {
			const pct = parseFloat(data && data.per_delivered) || 0;
			const clr = pct >= 100 ? "#059669" : pct > 0 ? "#d97706" : "#dc2626";
			value = `<span style="color:${clr};">${value}</span>`;
		}

		if (column.fieldname === "dn_status") {
			const color_map = {
				"Draft":     "#6b7280",
				"To Bill":   "#2563eb",
				"Completed": "#059669",
				"Cancelled": "#dc2626",
				"Return":    "#7c3aed",
			};
			const clr = color_map[data && data.dn_status] || "#6b7280";
			if (data && data.dn_status) {
				value = `<span style="color:${clr}; font-weight:600;">${value}</span>`;
			}
		}

		if (column.fieldname === "grand_total" || column.fieldname === "outstanding_amount"
			|| column.fieldname === "si_grand_total" || column.fieldname === "si_outstanding_amount") {
			const val = parseFloat(data && data[column.fieldname]) || 0;
			if (val > 0) {
				value = `<strong>${value}</strong>`;
			}
		}

		if (column.fieldname === "si_status") {
			const color_map = {
				"Draft":       "#6b7280",
				"Unpaid":      "#2563eb",
				"Partly Paid": "#d97706",
				"Paid":        "#059669",
				"Overdue":     "#dc2626",
				"Cancelled":   "#991b1b",
				"Return":      "#7c3aed",
			};
			const clr = color_map[data && data.si_status] || "#6b7280";
			if (data && data.si_status) {
				value = `<span style="color:${clr}; font-weight:600;">${value}</span>`;
			}
		}

		return value;
	},
};
