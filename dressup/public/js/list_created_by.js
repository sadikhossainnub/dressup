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

	// Helper method on ListView to filter list view by owner on click
	frappe.views.ListView.filter_by_owner = function (e, owner) {
		if (e) {
			e.preventDefault();
			e.stopPropagation();
		}
		if (cur_list && cur_list.filter_area) {
			cur_list.filter_area.add(cur_list.doctype, "owner", "=", owner);
		}
	};

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

		const owner_formatter = function (value) {
			if (!value) return "";
			const info = frappe.user_info ? frappe.user_info(value) : null;
			const fullname = (info && info.fullname) || value;
			const escaped_owner = frappe.utils.escape_html(value);
			const escaped_fullname = frappe.utils.escape_html(fullname);
			return `<a class="text-muted created-by-filter" href="#" onclick="frappe.views.ListView.filter_by_owner(event, '${escaped_owner}'); return false;" title="${__('Filter by {0}', [escaped_fullname])}">${escaped_fullname}</a>`;
		};

		// Register custom formatter
		if (!this.settings.formatters) {
			this.settings.formatters = {};
		}
		this.settings.formatters.owner = owner_formatter;

		if (!show) return;

		// Ensure 'owner' field is fetched in list query
		if (this.fields && !this.fields.some((f) => f[0] === "owner")) {
			this.fields.push(["owner", this.doctype]);
		}

		// Don't add if owner column already exists
		const already_has = this.columns.some(
			(c) => c.df && c.df.fieldname === "owner"
		);
		if (already_has) return;

		const owner_col = {
			type: "Field",
			df: {
				label: __("Created By"),
				fieldname: "owner",
				fieldtype: "Link",
				options: "User",
				formatter: owner_formatter,
			},
		};

		// Find the position of ID column (fieldname === "name")
		const name_col_idx = this.columns.findIndex(
			(c) => c.df && c.df.fieldname === "name"
		);

		if (name_col_idx !== -1) {
			// Insert right after the ID (name) column
			this.columns.splice(name_col_idx + 1, 0, owner_col);
		} else if (this.columns.length > 0) {
			// Insert after the first column (which is the primary ID/Subject column)
			this.columns.splice(1, 0, owner_col);
		} else {
			this.columns.push(owner_col);
		}
	};
}

// Execute immediately if ListView is already loaded, else wait for app_ready
if (window.frappe && frappe.views && frappe.views.ListView) {
	init_created_by_column();
} else {
	$(document).on("app_ready", init_created_by_column);
}

