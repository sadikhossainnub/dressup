// Copyright (c) 2026, Prime Technology of Bangladesh and contributors
// For license information, please see license.txt

frappe.query_reports["Attendance Trend Report"] = {
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
			fieldname: "department",
			label: __("Department"),
			fieldtype: "Link",
			options: "Department",
		},
		{
			fieldname: "employee",
			label: __("Employee"),
			fieldtype: "Link",
			options: "Employee",
			get_query: function () {
				let dept = frappe.query_report.get_filter_value("department");
				return dept ? { filters: { department: dept } } : {};
			},
		},
		{
			fieldname: "status",
			label: __("Status"),
			fieldtype: "Select",
			options: "\nPresent\nAbsent\nHalf Day\nOn Leave",
		},
		{
			fieldname: "shift",
			label: __("Shift"),
			fieldtype: "Link",
			options: "Shift Type",
		},
		{
			fieldname: "attendance_device_id",
			label: __("Attendance Device ID"),
			fieldtype: "Data",
		},
		{
			fieldname: "group_by",
			label: __("Group By"),
			fieldtype: "Select",
			options: "Employee\nDepartment\nMonth\nWeek",
			default: "Employee",
		},
	],

	formatter: function (value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data, default_formatter);

		if (column.fieldname === "attendance_percentage") {
			let pct = parseFloat(data && data.attendance_percentage) || 0;
			let color = pct >= 90 ? "#2ea44f" : pct >= 75 ? "#d97706" : "#dc2626";
			value = `<span style="color:${color}; font-weight:600;">${value}</span>`;
		}

		if (column.fieldname === "absent_days") {
			let absent = parseFloat(data && data.absent_days) || 0;
			if (absent > 0) {
				value = `<span style="color:#dc2626;">${value}</span>`;
			}
		}

		if (column.fieldname === "late_days") {
			let late = parseFloat(data && data.late_days) || 0;
			if (late > 0) {
				value = `<span style="color:#d97706;">${value}</span>`;
			}
		}

		return value;
	},
};
