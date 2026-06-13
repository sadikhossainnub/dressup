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
	},

	onload: function(listview) {
		// Status filter buttons
		const status_map = [
			{ label: __("Draft"),     docstatus: 0, color: "gray"  },
			{ label: __("Submitted"), docstatus: 1, color: "green" },
			{ label: __("Cancelled"), docstatus: 2, color: "red"   },
		];

		status_map.forEach(function(s) {
			listview.page.add_inner_button(s.label, function() {
				listview.filter_area.clear();
				listview.filter_area.add([
					["Cost Estimation", "docstatus", "=", s.docstatus]
				]);
				listview.refresh();
			});
		});

		// "All" button to clear the status filter
		listview.page.add_inner_button(__("All"), function() {
			// Remove only the docstatus filter if it exists
			const existing = listview.filter_area.filter_list.filters.find(
				f => f.fieldname === "docstatus"
			);
			if (existing) existing.remove();
			listview.refresh();
		});
	}
};
