frappe.listview_settings['Cost Estimation'] = {
	add_fields: ["docstatus"],
	get_indicator: function(doc) {
		if (doc.docstatus === 1) {
			return [__("Submitted"), "green", "docstatus,=,1"];
		} else if (doc.docstatus === 2) {
			return [__("Cancelled"), "red", "docstatus,=,2"];
		} else {
			return [__("Draft"), "gray", "docstatus,=,0"];
		}
	}
};
