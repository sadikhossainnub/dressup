// Copyright (c) 2024, DressUp and contributors
// For license information, please see license.txt

frappe.ui.form.on('Sketch Specification Sample Making Sheet', {
	refresh: function(frm) {
		if (frm.doc.docstatus === 1) {
			frm.add_custom_button(__('Cost Estimation'), function() {
				frappe.model.open_mapped_doc({
					method: 'dressup.dressup.doctype.sketch_specification_sample_making_sheet.sketch_specification_sample_making_sheet.make_cost_estimation',
					frm: frm
				});
			}, __('Create'));
		}
	},
	designer: function(frm) {
		if (frm.doc.designer && !frm.doc.design_no) {
			frappe.call({
				method: 'dressup.dressup.doctype.sketch_specification_sample_making_sheet.sketch_specification_sample_making_sheet.generate_design_no',
				args: { designer: frm.doc.designer },
				callback: function(r) {
					if (r.message) {
						frm.set_value('design_no', r.message);
					}
				}
			});
		}
	},
	frame_cost: function(frm) {
		if (frm.doc.frame_cost) {
			frm.set_value('cost_for_30_unit', frm.doc.frame_cost * 30);
		}
	},
	process_cost: function(frm) {
		if (frm.doc.process_cost) {
			frm.set_value('cost_for_50_unit', frm.doc.process_cost * 50);
		}
	},
	chemical_cost: function(frm) {
		if (frm.doc.chemical_cost) {
			frm.set_value('cost_for_70_unit', frm.doc.chemical_cost * 70);
		}
	},
	print_cost: function(frm) {
		if (frm.doc.print_cost) {
			frm.set_value('cost_for_100_unit', frm.doc.print_cost * 100);
		}
	}
});