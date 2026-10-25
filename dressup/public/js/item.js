// Copyright (c) 2026, Prime Technology of Bangladesh and contributors
// For license information, please see license.txt

frappe.ui.form.on('Item', {
	refresh: function(frm) {
		setup_description_values_grid(frm);
		setup_preview_button(frm);
		setup_download_upload_buttons(frm);
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

function setup_download_upload_buttons(frm) {
	// Download Description Values as Excel/CSV
	if (frm.doc.description_template && frm.doc.description_values && frm.doc.description_values.length > 0) {
		frm.add_custom_button(__('Download Description Values'), function() {
			download_description_values(frm);
		}, __('Description Template'));
	}

	// Upload Description Values from Excel/CSV
	if (frm.doc.description_template) {
		frm.add_custom_button(__('Upload Description Values'), function() {
			upload_description_values(frm);
		}, __('Description Template'));
	}
}

function download_description_values(frm) {
	if (!frm.doc.description_values || frm.doc.description_values.length === 0) {
		frappe.msgprint({
			title: __('No Data'),
			message: __('No description values to download.'),
			indicator: 'orange'
		});
		return;
	}

	// Prepare data for export
	let data = frm.doc.description_values.map(row => ({
		'Field Key': row.field_key || '',
		'Field Label': row.field_label || '',
		'Value': row.value || ''
	}));

	// Convert to CSV
	let csv_content = [];
	let headers = Object.keys(data[0]);
	csv_content.push(headers.join(','));

	data.forEach(row => {
		let values = headers.map(header => {
			let value = row[header] || '';
			// Escape commas and quotes in CSV
			if (value.toString().includes(',') || value.toString().includes('"') || value.toString().includes('\n')) {
				value = '"' + value.toString().replace(/"/g, '""') + '"';
			}
			return value;
		});
		csv_content.push(values.join(','));
	});

	let csv_string = csv_content.join('\n');
	
	// Download file
	let filename = `${frm.doc.item_code || frm.doc.name}_description_values.csv`;
	let blob = new Blob([csv_string], { type: 'text/csv;charset=utf-8;' });
	
	if (navigator.msSaveBlob) { // IE 10+
		navigator.msSaveBlob(blob, filename);
	} else {
		let link = document.createElement('a');
		if (link.download !== undefined) {
			let url = URL.createObjectURL(blob);
			link.setAttribute('href', url);
			link.setAttribute('download', filename);
			link.style.visibility = 'hidden';
			document.body.appendChild(link);
			link.click();
			document.body.removeChild(link);
		}
	}

	frappe.show_alert({
		message: __('Description values downloaded successfully'),
		indicator: 'green'
	}, 3);
}

function upload_description_values(frm) {
	if (!frm.doc.description_template) {
		frappe.msgprint({
			title: __('No Template Selected'),
			message: __('Please select a Description Template first.'),
			indicator: 'orange'
		});
		return;
	}

	let upload_dialog = new frappe.ui.Dialog({
		title: __('Upload Description Values'),
		fields: [
			{
				fieldtype: 'HTML',
				fieldname: 'upload_instructions',
				options: `
					<div class="alert alert-info">
						<strong>${__('Instructions:')}</strong>
						<ul style="margin-bottom: 0; padding-left: 20px;">
							<li>${__('Upload a CSV file with columns: Field Key, Field Label, Value')}</li>
							<li>${__('You can download current values, modify them, and upload back')}</li>
							<li>${__('Field Key and Field Label must match the template fields')}</li>
							<li>${__('Only the Value column will be updated')}</li>
						</ul>
					</div>
				`
			},
			{
				fieldtype: 'Attach',
				fieldname: 'csv_file',
				label: __('Select CSV File'),
				reqd: 1
			}
		],
		primary_action_label: __('Upload'),
		primary_action: function(values) {
			if (!values.csv_file) {
				frappe.msgprint(__('Please select a file'));
				return;
			}

			frappe.call({
				method: 'dressup.api.parse_description_values_csv',
				args: {
					file_url: values.csv_file
				},
				freeze: true,
				freeze_message: __('Processing CSV file...'),
				callback: function(r) {
					if (r && r.message) {
						update_description_values_from_upload(frm, r.message);
						upload_dialog.hide();
						frappe.show_alert({
							message: __('Description values uploaded successfully'),
							indicator: 'green'
						}, 3);
					}
				}
			});
		}
	});

	upload_dialog.show();
}

function update_description_values_from_upload(frm, uploaded_data) {
	// Create a map of existing rows by field_key
	let existing_map = {};
	(frm.doc.description_values || []).forEach(row => {
		if (row.field_key) {
			existing_map[row.field_key] = row;
		}
	});

	// Update values from uploaded data
	uploaded_data.forEach(upload_row => {
		let field_key = upload_row.field_key || upload_row['Field Key'];
		let value = upload_row.value || upload_row['Value'];

		if (field_key && existing_map[field_key]) {
			existing_map[field_key].value = value || '';
		}
	});

	frm.refresh_field('description_values');
	frm.dirty();
}

