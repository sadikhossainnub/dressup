// Frappe v16 compatible: Add "Created By" (owner) column to all DocType list views.
//
// Root cause analysis (v16):
// - setup_columns() builds columns from in_list_view DocFields only (owner is NOT a DocField)
// - reorder_listview_fields() then REPLACES this.columns with only what's in list_view_settings.fields
// - So any column pushed after setup_columns but before reorder runs gets wiped
//
// Correct v16 approach:
// - Patch setup_columns() to append owner AFTER reorder_listview_fields() runs (at the end)
// - Read show_created_by from this.list_view_settings (saved in DB via the patched DocType)

function init_created_by_column() {
	if (!frappe.views || !frappe.views.ListView) return;

	// Guard against double-patching
	if (frappe.views.ListView.prototype._created_by_patched) return;
	frappe.views.ListView.prototype._created_by_patched = true;

	const _original_setup_columns = frappe.views.ListView.prototype.setup_columns;

	frappe.views.ListView.prototype.setup_columns = function () {
		// Run the original setup_columns (includes reorder_listview_fields inside)
		_original_setup_columns.call(this);

		// NOW safely check the setting — by this point reorder is already done
		const settings = this.list_view_settings || {};
		const show = cint(settings.show_created_by) === 1;

		if (!show) return;

		// Don't add if owner column already exists
		const already_has = this.columns.some(
			(c) => c.df && c.df.fieldname === "owner"
		);
		if (already_has) return;

		// Append owner column at the end (before ID column which is last)
		// Find the position: insert before the trailing "name" column if present
		const name_col_idx = this.columns.findLastIndex(
			(c) => c.type === "Field" && c.df && c.df.fieldname === "name"
		);

		const owner_col = {
			type: "Field",
			df: {
				label: __("Created By"),
				fieldname: "owner",
				fieldtype: "Link",
				options: "User",
			},
		};

		if (name_col_idx !== -1) {
			// Insert just before the trailing ID/name column
			this.columns.splice(name_col_idx, 0, owner_col);
		} else {
			this.columns.push(owner_col);
		}

		// Register a custom formatter so it shows Full Name instead of email
		if (!this.settings.formatters) {
			this.settings.formatters = {};
		}
		if (!this.settings.formatters.owner) {
			this.settings.formatters.owner = function (value) {
				if (!value) return "";
				const fullname = frappe.user.full_name(value) || value;
				return `<a class="text-muted" href="/app/user/${encodeURIComponent(value)}">${frappe.utils.escape_html(fullname)}</a>`;
			};
		}
	};
}

// Execute immediately if ListView is already loaded, else wait for app_ready
if (window.frappe && frappe.views && frappe.views.ListView) {
	init_created_by_column();
} else {
	$(document).on("app_ready", init_created_by_column);
}
