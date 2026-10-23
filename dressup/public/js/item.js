// Copyright (c) 2026, Prime Technology of Bangladesh and contributors
// For license information, please see license.txt

frappe.ui.form.on('Item', {
	refresh: function(frm) {
		setup_description_values_grid(frm);
		setup_preview_button(frm);
		set_template_query(frm);
	},

	onload_post_render: function(frm) {
		setup_description_values_grid(frm);
	},

	description_template: function(frm) {
		if (!frm.doc.description_template) {
			frm.clear_table('description_values');
			frm.refresh_field('description_values');
			return;
		}

		frappe.db.get_doc('Item Description Template', frm.doc.description_template)
			.then(template => {
				frm.clear_table('description_values');
				if (template && template.fields && template.fields.length) {
					template.fields.forEach(field => {
						let row = frm.add_child('description_values');
						row.field_key = field.field_key;
						row.field_label = field.field_label;
						row.value = field.default_value || '';
					});
				}
				frm.refresh_field('description_values');
				setup_description_values_grid(frm);
			});
	}
});

function set_template_query(frm) {
	frm.set_query('description_template', function() {
		return {
			filters: {
				enabled: 1
			}
		};
	});
}

function setup_description_values_grid(frm) {
	if (!frm.fields_dict.description_values || !frm.fields_dict.description_values.grid) {
		return;
	}

	let grid = frm.fields_dict.description_values.grid;

	// Disable add/delete rows to preserve template structure
	frm.set_df_property('description_values', 'cannot_add_rows', true);
	frm.set_df_property('description_values', 'cannot_delete_rows', true);
	grid.cannot_add_rows = true;
	grid.cannot_delete_rows = true;

	// Ensure field_key and field_label are read-only; value is editable
	grid.toggle_enable('field_key', false);
	grid.toggle_enable('field_label', false);
	grid.toggle_enable('value', true);
}

function setup_preview_button(frm) {
	// Add custom button to preview rendered description without saving
	frm.add_custom_button(__('Preview Description'), function() {
		if (!frm.doc.description_template) {
			frappe.msgprint({
				title: __('No Template Selected'),
				message: __('Please select a Description Template first.'),
				indicator: 'orange'
			});
			return;
		}

		let values = (frm.doc.description_values || []).map(row => ({
			field_key: row.field_key,
			value: row.value || ''
		}));

		frappe.call({
			method: 'dressup.api.preview_item_description',
			args: {
				template_name: frm.doc.description_template,
				values: values,
				item_code: frm.doc.item_code || '',
				item_name: frm.doc.item_name || '',
				brand: frm.doc.brand || '',
				item_group: frm.doc.item_group || ''
			},
			freeze: true,
			freeze_message: __('Rendering description preview...'),
			callback: function(r) {
				if (r && r.message) {
					let d = new frappe.ui.Dialog({
						title: __('Description Preview — {0}', [frm.doc.description_template]),
						fields: [
							{
								fieldtype: 'HTML',
								fieldname: 'preview_html'
							}
						],
						size: 'large'
					});
					d.fields_dict.preview_html.$wrapper.html(r.message);
					d.show();
				}
			}
		});
	});
}

