// Globally add "Created By" (owner) column to all DocType list views.
// NOTE: owner data is already fetched via frappe.model.std_fields_list,
// so we only need to add the column definition for display if selected in settings.

function init_created_by_column() {
	if (!frappe.views || !frappe.views.ListView) return;

	if (frappe.views.ListView.prototype.setup_columns_patched) return;
	frappe.views.ListView.prototype.setup_columns_patched = true;

	const _setup_columns = frappe.views.ListView.prototype.setup_columns;
	frappe.views.ListView.prototype.setup_columns = function () {
		_setup_columns.call(this);

		console.log("ListView setup_columns called for:", this.doctype);
		console.log("this.list_view_settings:", this.list_view_settings);

		// Handle both standard and nested list_view_settings structure due to save_listview_settings callback
		let settings = this.list_view_settings || {};
		if (settings.listview_settings) {
			settings = settings.listview_settings;
		}

		console.log("Evaluated show_created_by:", settings.show_created_by);

		if (cint(settings.show_created_by) === 1) {
			// Don't add if owner column already exists
			const has_owner_col = this.columns.some(
				(c) => c.df && c.df.fieldname === "owner"
			);

			console.log("has_owner_col:", has_owner_col);

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
				console.log("Added owner column to columns list!");
			}

			// Custom formatter to show User's Full Name instead of Email ID
			if (!this.settings.formatters) {
				this.settings.formatters = {};
			}
			this.settings.formatters.owner = function (value) {
				if (!value) return "";
				const fullname = frappe.user.full_name(value) || value;
				return `<a class="text-muted" href="/app/user/${encodeURIComponent(value)}">${frappe.utils.escape_html(fullname)}</a>`;
			};
		}
	};
}

if (window.frappe && frappe.views && frappe.views.ListView) {
	init_created_by_column();
} else {
	$(document).on("app_ready", init_created_by_column);
}
