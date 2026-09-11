// Copyright (c) 2026, Prime Technology of Bangladesh and contributors
// For license information, please see license.txt

frappe.query_reports["Sales Order vs Delivery Note"] = {
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
			fieldname: "date_based_on",
			label: __("Date Based On"),
			fieldtype: "Select",
			options: "Sales Order Date\nDelivery Note Date",
			default: "Sales Order Date",
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
			fieldname: "item_code",
			label: __("Item Code"),
			fieldtype: "Link",
			options: "Item",
		},
		{
			fieldname: "so_status",
			label: __("SO Status"),
			fieldtype: "Select",
			options: "\nDraft\nOn Hold\nTo Deliver and Bill\nTo Bill\nTo Deliver\nCompleted\nCancelled\nClosed",
		},
		{
			fieldname: "delivery_status",
			label: __("Delivery Status"),
			fieldtype: "Select",
			options: "\nNot Delivered\nPartially Delivered\nFully Delivered",
		},
		{
			fieldname: "dn_status",
			label: __("DN Status"),
			fieldtype: "Select",
			options: "\nDraft\nTo Bill\nCompleted\nCancelled\nReturn",
		},
	],

	formatter: function (value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data, default_formatter);

		// SO Status colour
		if (column.fieldname === "so_status") {
			const color_map = {
				"Draft":                "#6b7280",
				"On Hold":             "#d97706",
				"To Deliver and Bill": "#2563eb",
				"To Bill":             "#7c3aed",
				"To Deliver":          "#0891b2",
				"Completed":           "#059669",
				"Cancelled":           "#dc2626",
				"Closed":              "#374151",
			};
			const clr = color_map[(data && data.so_status)] || "#6b7280";
			if (data && data.so_status) {
				value = `<span style="color:${clr}; font-weight:600;">${value}</span>`;
			}
		}

		// Delivery Status colour
		if (column.fieldname === "delivery_status") {
			const color_map = {
				"Not Delivered":       "#dc2626",
				"Partially Delivered": "#d97706",
				"Fully Delivered":     "#059669",
			};
			const clr = color_map[(data && data.delivery_status)] || "#6b7280";
			if (data && data.delivery_status) {
				value = `<span style="color:${clr}; font-weight:600;">${value}</span>`;
			}
		}

		// % Delivered colour
		if (column.fieldname === "per_delivered") {
			const pct = parseFloat((data && data.per_delivered) || 0);
			const clr = pct >= 100 ? "#059669" : pct > 0 ? "#d97706" : "#dc2626";
			value = `<span style="color:${clr};">${value}</span>`;
		}

		// DN Status colour
		if (column.fieldname === "dn_status") {
			const color_map = {
				"Draft":     "#6b7280",
				"To Bill":   "#2563eb",
				"Completed": "#059669",
				"Cancelled": "#dc2626",
				"Return":    "#7c3aed",
			};
			const clr = color_map[(data && data.dn_status)] || "#6b7280";
			if (data && data.dn_status) {
				value = `<span style="color:${clr}; font-weight:600;">${value}</span>`;
			}
		}

		// Pending qty — highlight if > 0
		if (column.fieldname === "pending_qty") {
			const qty = parseFloat((data && data.pending_qty) || 0);
			if (qty > 0) {
				value = `<span style="color:#dc2626; font-weight:600;">${value}</span>`;
			} else if (qty === 0) {
				value = `<span style="color:#059669; font-weight:600;">${value}</span>`;
			}
		}

		// Highlight SO Qty / DN Qty
		if (column.fieldname === "so_qty" || column.fieldname === "dn_qty") {
			const qty = parseFloat((data && data[column.fieldname]) || 0);
			if (qty > 0) {
				value = `<strong>${value}</strong>`;
			}
		}

		return value;
	},
};
