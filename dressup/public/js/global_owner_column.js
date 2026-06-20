// Global "Created By" (Owner) column for ALL List Views
frappe.provide("frappe.listview_settings");

$(document).on("page-change", function () {
	setup_owner_column();
});

frappe.router.on("change", function () {
	setTimeout(setup_owner_column, 500);
});

function setup_owner_column() {
	let route = frappe.get_route();
	if (!route || route[0] !== "List") return;

	let doctype = route[1];
	if (!doctype) return;

	// Wait for list view to be ready
	frappe.after_ajax(() => {
		let list_view = cur_list;
		if (!list_view || list_view.doctype !== doctype) return;

		// Add 'owner' to the list view fields if not already present
		if (list_view.meta && !list_view.columns_map?.["owner"]) {
			inject_owner_column(list_view);
		}
	});
}

function inject_owner_column(list_view) {
	try {
		// Add owner field to fields list so it's fetched
		if (!list_view.fields.includes("owner")) {
			list_view.fields.push("owner");
		}

		// Add column definition
		if (list_view.columns && !list_view.columns.find(c => c.field === "owner" || c.fieldname === "owner" || (c.df && c.df.fieldname === "owner"))) {
			list_view.columns.push({
				type: "Field",
				field: "owner",
				fieldname: "owner",
				df: {
					label: __("Created By"),
					fieldname: "owner",
					fieldtype: "Data",
				},
			});
		}

		// Update columns_map to prevent re-injection
		if (list_view.columns_map) {
			list_view.columns_map["owner"] = true;
		}

		list_view.refresh();
	} catch (e) {
		console.warn("Owner column injection failed:", e);
	}
}
