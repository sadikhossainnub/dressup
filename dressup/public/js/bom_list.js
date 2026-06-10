frappe.listview_settings["BOM"] = {
	add_fields: ["custom_bom_creator", "custom_bom_type", "is_active", "is_default"],

	get_indicator(doc) {
		if (doc.is_active) {
			return [__("Active"), "green", "is_active,=,1"];
		} else if (doc.docstatus === 2) {
			return [__("Cancelled"), "red", "docstatus,=,2"];
		} else {
			return [__("Not Active"), "gray", "is_active,=,0"];
		}
	},

	formatters: {
		custom_bom_creator(value) {
			if (value) {
				return `<span class="indicator-pill whitespace-nowrap ellipsis orange">
					<span class="ellipsis">${frappe.utils.escape_html(value)}</span>
				</span>`;
			}
			return "";
		},
	},
};
