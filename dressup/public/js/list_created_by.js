// Globally add "Created By" (owner) column to all DocType list views.
// NOTE: owner data is already fetched via frappe.model.std_fields_list,
// so we only need to add the column definition for display if selected in settings.
$(document).on("app_ready", function () {
	if (!frappe.views || !frappe.views.ListView) return;

	const _setup_columns = frappe.views.ListView.prototype.setup_columns;
	frappe.views.ListView.prototype.setup_columns = function () {
		_setup_columns.call(this);

		if (this.list_view_settings && cint(this.list_view_settings.show_created_by) === 1) {
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
		}
	};
});
