// Globally add "Created By" (owner) column to all DocType list views.
// NOTE: owner data is already fetched via frappe.model.std_fields_list,
// so we only need to add the column definition for display.
$(document).on("app_ready", function () {
	if (!frappe.views || !frappe.views.ListView) return;

	const _build_columns = frappe.views.ListView.prototype.build_columns;
	frappe.views.ListView.prototype.build_columns = function () {
		_build_columns.call(this);

		// Don't add if owner column already exists
		const has_owner_col = this.columns.some(
			(c) => c.df && c.df.fieldname === "owner"
		);

		if (!has_owner_col) {
			this.columns.push({
				type: "Field",
				df: {
					label: __("Created By"),
					fieldname: "owner",
					fieldtype: "Link",
					options: "User",
				},
			});
		}
	};
});
