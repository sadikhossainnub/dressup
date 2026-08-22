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

function get_configured_fieldnames(settings) {
	if (!settings || !settings.fields) return [];
	let fields = settings.fields;
	if (typeof fields === "string") {
		try {
			fields = JSON.parse(fields);
		} catch (e) {
			return [];
		}
	}
	if (!Array.isArray(fields)) return [];

	return fields
		.map((f) => {
			if (typeof f === "string") return f;
			if (Array.isArray(f)) return f[0];
			if (typeof f === "object" && f !== null) return f.fieldname || f.value;
			return null;
		})
		.filter(Boolean);
}

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

		// Ensure virtual 'owner' meta field exists so list settings dialog can pick it up
		if (this.meta && this.meta.fields && !this.meta.fields.some((f) => f.fieldname === "owner")) {
			this.meta.fields.push({
				fieldname: "owner",
				label: __("Created By"),
				fieldtype: "Link",
				options: "User",
				read_only: 1,
			});
		}

		// Check settings and dynamic field ordering
		const settings = this.list_view_settings || {};
		const configured_fields = get_configured_fieldnames(settings);
		const is_in_configured = configured_fields.includes("owner");
		const show = is_in_configured || cint(settings.show_created_by) === 1;

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

		if (is_in_configured) {
			const owner_idx_in_config = configured_fields.indexOf("owner");
			let inserted = false;

			// Look backward in configured fields for a column present in this.columns
			for (let i = owner_idx_in_config - 1; i >= 0; i--) {
				const prev_field = configured_fields[i];
				const prev_col_idx = this.columns.findIndex(
					(c) => c.df && c.df.fieldname === prev_field
				);
				if (prev_col_idx !== -1) {
					this.columns.splice(prev_col_idx + 1, 0, owner_col);
					inserted = true;
					break;
				}
			}

			// Look forward if no preceding field was found
			if (!inserted) {
				for (let i = owner_idx_in_config + 1; i < configured_fields.length; i++) {
					const next_field = configured_fields[i];
					const next_col_idx = this.columns.findIndex(
						(c) => c.df && c.df.fieldname === next_field
					);
					if (next_col_idx !== -1) {
						this.columns.splice(next_col_idx, 0, owner_col);
						inserted = true;
						break;
					}
				}
			}

			if (!inserted) {
				this.columns.push(owner_col);
			}
		} else {
			// Default placement: right after 'name' column or 2nd column
			const name_col_idx = this.columns.findIndex(
				(c) => c.df && c.df.fieldname === "name"
			);

			if (name_col_idx !== -1) {
				this.columns.splice(name_col_idx + 1, 0, owner_col);
			} else if (this.columns.length > 0) {
				this.columns.splice(1, 0, owner_col);
			} else {
				this.columns.push(owner_col);
			}
		}
	};

	// -------------------------------------------------------------------------
	// Patch List View Settings Dialog to render "Show Created By" checkbox
	// -------------------------------------------------------------------------

	if (frappe.views.ListView.prototype.get_list_settings_fields) {
		const _original_get_fields = frappe.views.ListView.prototype.get_list_settings_fields;
		frappe.views.ListView.prototype.get_list_settings_fields = function () {
			const fields = _original_get_fields.call(this) || [];
			if (!fields.some((f) => f.fieldname === "show_created_by")) {
				fields.push({
					fieldname: "show_created_by",
					fieldtype: "Check",
					label: __("Show Created By"),
					default: cint(this.list_view_settings ? this.list_view_settings.show_created_by : 0),
				});
			}
			return fields;
		};
	}

	if (frappe.views.ListView.prototype.show_list_settings_dialog) {
		const _original_show_dialog = frappe.views.ListView.prototype.show_list_settings_dialog;
		frappe.views.ListView.prototype.show_list_settings_dialog = function () {
			_original_show_dialog.call(this);

			const dialog =
				this.list_settings_dialog ||
				this.settings_dialog ||
				(cur_dialog && (cur_dialog.title === __("List Settings") || cur_dialog.title === __("List View Settings"))
					? cur_dialog
					: null);

			if (dialog && !dialog.has_field("show_created_by")) {
				dialog.add_field({
					fieldname: "show_created_by",
					fieldtype: "Check",
					label: __("Show Created By"),
					default: cint(this.list_view_settings ? this.list_view_settings.show_created_by : 0),
				});
				if (this.list_view_settings && this.list_view_settings.show_created_by !== undefined) {
					dialog.set_value("show_created_by", cint(this.list_view_settings.show_created_by));
				}
			}
		};
	}
}

// Execute immediately if ListView is already loaded, else wait for app_ready
if (window.frappe && frappe.views && frappe.views.ListView) {
	init_created_by_column();
} else {
	$(document).on("app_ready", init_created_by_column);
}

