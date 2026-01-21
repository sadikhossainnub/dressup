// Copyright (c) 2024, DressUp and contributors
// For license information, please see license.txt

frappe.ui.form.on('Sketch Specification Sample Making Sheet', {
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
								method: 'dressup.dressup.doctype.sketch_specification_sample_making_sheet.sketch_specification_sample_making_sheet.make_cost_estimation',
								frm: frm
							});
						}, __('Create'));
					}
				}
			});

		}
		toggle_color_fields(frm);
		render_image_previews(frm);
	},
	additional_images_add: function (frm) {
		render_image_previews(frm);
	},
	additional_images_remove: function (frm) {
		render_image_previews(frm);
	},
	onload: function (frm) {
		toggle_color_fields(frm);
	},
	color_units: function (frm) {
		toggle_color_fields(frm);
	},
	designer: function (frm) {
		if (frm.doc.designer) {
			// Generate design no if empty OR if it's currently an Employee ID (EID-xxxx)
			if (!frm.doc.design_no || frm.doc.design_no.startsWith('EID-')) {
				frappe.call({
					method: 'dressup.dressup.doctype.sketch_specification_sample_making_sheet.sketch_specification_sample_making_sheet.generate_design_no',
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

var toggle_color_fields = function (frm) {
	let units = parseInt(frm.doc.color_units) || 0;

	frm.toggle_display('color', units >= 1);
	frm.toggle_display('data_xmgl', units >= 1);

	frm.toggle_display('color_2', units >= 2);
	frm.toggle_display('data_ryzm', units >= 2);

	frm.toggle_display('color_3', units >= 3);
	frm.toggle_display('data_muzc', units >= 3);

	frm.toggle_display('color_4', units >= 4);
	frm.toggle_display('data_lfwb', units >= 4);

	frm.toggle_display('color_5', units >= 5);
	frm.toggle_display('data_hnjh', units >= 5);

	frm.toggle_display('color_6', units >= 6);
	frm.toggle_display('data_zsdd', units >= 6);

	frm.toggle_display('color_7', units >= 7);
	frm.toggle_display('data_uxrz', units >= 7);

	frm.toggle_display('color_8', units >= 8);
	frm.toggle_display('data_mnat', units >= 8);

	frm.toggle_display('color_9', units >= 9);
	frm.toggle_display('data_wptw', units >= 9);

	frm.toggle_display('color_10', units >= 10);
	frm.toggle_display('data_znsh', units >= 10);
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