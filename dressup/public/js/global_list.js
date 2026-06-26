// Add "Created By" (owner) column to all DocType list views
frappe.listview_settings[""] = frappe.listview_settings[""] || {};

$(document).on("app_ready", function () {
	const _get_fields = frappe.views.ListView.prototype.get_fields;
	frappe.views.ListView.prototype.get_fields = function () {
		let fields = _get_fields.call(this);
		// owner already a default_field, just push if not present
		const has_owner = fields.some((f) => {
			if (typeof f === "string") {
				return f === "owner" || f.endsWith(".`owner`") || f.endsWith(".owner");
			}
			return (Array.isArray(f) ? f[0] : f) === "owner";
		});
		if (!has_owner) {
			fields.push(frappe.model.get_full_column_name("owner", this.doctype));
		}
		return fields;
	};
});
