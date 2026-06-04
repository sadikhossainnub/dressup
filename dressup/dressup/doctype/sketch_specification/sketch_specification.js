// Copyright (c) 2024, DressUp and contributors
// For license information, please see license.txt

frappe.ui.form.on('Sketch Specification', {
	refresh: function (frm) {
		if (frm.doc.docstatus === 1) {
			frappe.call({
				method: 'frappe.client.get_count',
				args: {
					doctype: 'Cost Estimation',
					filters: { tech_pack_no: frm.doc.name }
				},
				callback: function (r) {
					if (!r.message || r.message === 0) {
						frm.add_custom_button(__('Cost Estimation'), function () {
							frappe.model.open_mapped_doc({
								method: 'dressup.dressup.doctype.sketch_specification.sketch_specification.make_cost_estimation',
								frm: frm
							});
						}, __('Create'));
					}
				}
			});

			frappe.call({
				method: 'frappe.client.get_count',
				args: {
					doctype: 'Measurement Chart',
					filters: { style_no: frm.doc.design_no }
				},
				callback: function (r) {
					if (!r.message || r.message === 0) {
						frm.add_custom_button(__('Measurement Chart'), function () {
							frappe.model.open_mapped_doc({
								method: 'dressup.dressup.doctype.sketch_specification.sketch_specification.make_measurement_chart',
								frm: frm
							});
						}, __('Create'));
					}
				}
			});
		}

		toggle_artwork_color_fields(frm);
		render_image_previews(frm);
	},
	additional_images_add: function (frm) {
		render_image_previews(frm);
	},
	additional_images_remove: function (frm) {
		render_image_previews(frm);
	},
	onload: function (frm) {
		toggle_artwork_color_fields(frm);
	},


	designer: function (frm) {
		if (frm.doc.designer) {
			// Generate design no if empty OR if it's currently an Employee ID (EID-xxxx)
			if (!frm.doc.design_no || frm.doc.design_no.startsWith('EID-')) {
				frappe.call({
					method: 'dressup.dressup.doctype.sketch_specification.sketch_specification.generate_design_no',
					args: { designer: frm.doc.designer },
					callback: function (r) {
						if (r.message) {
							frm.set_value('design_no', r.message);
						}
					}
				});
			}
		}
	},


	image: function (frm) {
		render_image_previews(frm);
	}
});

frappe.ui.form.on('Sketch Specification Image', {
	image: function (frm, cdt, cdn) {
		render_image_previews(frm);
	},
	description: function (frm, cdt, cdn) {
		render_image_previews(frm);
	}
});

frappe.ui.form.on('Sketch TP Image', {
	name1: function (frm, cdt, cdn) {
		toggle_artwork_color_fields(frm);
	},
	table_jtfk_add: function (frm, cdt, cdn) {
		toggle_artwork_color_fields(frm);
	},
	table_jtfk_remove: function (frm, cdt, cdn) {
		toggle_artwork_color_fields(frm);
	}
});

var toggle_artwork_color_fields = function (frm) {
	// Check which artwork types exist in the child table
	let rows = frm.doc.table_jtfk || [];
	let has_top_artwork = rows.some(r => r.name1 === 'Top Artwork');
	let has_koti_artwork = rows.some(r => r.name1 === 'Koti Artwork');
	let has_bottom_artwork = rows.some(r => r.name1 === 'Bottom Artwork');
	let has_dupatta_artwork = rows.some(r => r.name1 === 'Dupatta Artwork');

	frm.toggle_display('body_artwork_colors', has_top_artwork);
	frm.toggle_display('koti_artwork_colors', has_koti_artwork);
	frm.toggle_display('bottom_artwork_colors', has_bottom_artwork);
	frm.toggle_display('dupatta_artwork_colors', has_dupatta_artwork);
};

var render_image_previews = function (frm) {
	let html = '<div style="display: flex; flex-wrap: wrap; gap: 15px; margin: 15px 0; padding: 15px; background: #f8f9fa; border-radius: 8px; border: 1px solid #e9ecef;">';
	let has_images = false;

	if (frm.doc.image) {
		has_images = true;
		html += `
            <div style="background: white; border: 1px solid #dee2e6; padding: 8px; border-radius: 6px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                <img src="${frm.doc.image}" style="width: 160px; height: 160px; object-fit: contain; display: block; border-radius: 4px; cursor: pointer;" onclick="window.open('${frm.doc.image}')">
                <div style="text-align: center; font-size: 11px; margin-top: 8px; font-weight: 600; color: #495057;">MAIN SKETCH</div>
            </div>`;
	}

	(frm.doc.additional_images || []).forEach((row, i) => {
		if (row.image) {
			has_images = true;
			html += `
                <div style="background: white; border: 1px solid #dee2e6; padding: 8px; border-radius: 6px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                    <img src="${row.image}" style="width: 160px; height: 160px; object-fit: contain; display: block; border-radius: 4px; cursor: pointer;" onclick="window.open('${row.image}')">
                    <div style="text-align: center; font-size: 11px; margin-top: 8px; font-weight: 500; color: #6c757d;">${row.description || 'Image ' + (i + 1)}</div>
                </div>`;
		}
	});

	if (!has_images) {
		html += '<div style="color: #adb5bd; font-style: italic; padding: 20px;">No images attached yet.</div>';
	}

	html += '</div>';

	if (frm.fields_dict.image_previews) {
		frm.fields_dict.image_previews.$wrapper.html(html);
	}
};
