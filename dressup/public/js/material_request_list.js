frappe.listview_settings["Material Request"] = frappe.listview_settings["Material Request"] || {};

if (!frappe.listview_settings["Material Request"].add_fields) {
	frappe.listview_settings["Material Request"].add_fields = [];
}
if (!frappe.listview_settings["Material Request"].add_fields.includes("owner")) {
	frappe.listview_settings["Material Request"].add_fields.push("owner");
}

const original_onload = frappe.listview_settings["Material Request"].onload;
frappe.listview_settings["Material Request"].onload = function (listview) {
	if (original_onload) {
		original_onload.call(this, listview);
	}

	const has_owner = listview.columns.some(col => col.df && col.df.fieldname === "owner");
	if (!has_owner) {
		listview.columns.push({
			type: "Field",
			df: {
				label: __("Owner"),
				fieldname: "owner",
				fieldtype: "Data",
			},
		});
	}
};
