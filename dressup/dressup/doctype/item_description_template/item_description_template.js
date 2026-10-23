// Copyright (c) 2026, Prime Technology of Bangladesh and contributors
// For license information, please see license.txt

frappe.ui.form.on('Item Description Template', {
	refresh: function(frm) {
		// Preview button
		frm.add_custom_button(__('Preview'), function() {
			let preview_values = {};
			(frm.doc.fields || []).forEach(f => {
				preview_values[f.field_key] = f.default_value || `[${f.field_label || f.field_key}]`;
			});

			frappe.call({
				method: 'dressup.api.preview_item_description',
				args: {
					template_name: frm.doc.name,
					template_html: frm.doc.template_html,
					values: preview_values,
					item_code: 'SAMPLE-ITEM-001',
					item_name: 'Sample Garment Item',
					brand: 'DressUp Brand',
					item_group: 'Garments'
				},
				callback: function(r) {
					if (r && r.message) {
						let d = new frappe.ui.Dialog({
							title: __('Template Preview — {0}', [frm.doc.template_name || frm.doc.name]),
							fields: [
								{
									fieldtype: 'HTML',
									fieldname: 'preview_area'
								}
							],
							size: 'large'
						});
						d.fields_dict.preview_area.$wrapper.html(r.message);
						d.show();
					}
				}
			});
		});

		// Bulk regenerate button (System Manager only)
		if (!frm.is_new() && frappe.user.has_role('System Manager')) {
			frm.add_custom_button(__('Regenerate Descriptions for Items'), function() {
				frappe.confirm(
					__('Are you sure you want to regenerate descriptions for all Items using template "{0}"? This job runs in the background.', [frm.doc.template_name || frm.doc.name]),
					function() {
						frappe.call({
							method: 'dressup.api.regenerate_item_descriptions',
							args: {
								template: frm.doc.name
							},
							freeze: true,
							freeze_message: __('Enqueuing regeneration job...'),
							callback: function(r) {
								if (r && r.message) {
									frappe.msgprint({
										title: __('Job Enqueued'),
										message: r.message.message || __('Background regeneration job enqueued successfully.'),
										indicator: 'green'
									});
								}
							}
						});
					}
				);
			}, __('Actions'));
		}
	}
});

