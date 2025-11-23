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
	}
});