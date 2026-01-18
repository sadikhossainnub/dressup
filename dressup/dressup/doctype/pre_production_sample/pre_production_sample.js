// Copyright (c) 2025, Prime Technology of Bangladesh and contributors
// For license information, please see license.txt

frappe.ui.form.on("Pre Production Sample", {
	refresh(frm) {
		if (!frm.doc.__islocal && frm.doc.docstatus === 0) {
			frm.add_custom_button(__('Fetch Tech Pack Data'), function () {
				frm.trigger('fetch_tech_pack_data');
			});
		}

		if (frm.doc.docstatus === 1) {
			frm.add_custom_button(__('Quality Inspection'), function () {
				frappe.model.open_mapped_doc({
					method: 'dressup.dressup.doctype.pre_production_sample.pre_production_sample.make_quality_inspection',
					frm: frm
				});
			}, __('Create'));
		}
	},

	tech_pack_no(frm) {
		if (frm.doc.tech_pack_no) {
			frm.trigger('fetch_tech_pack_data');
		}
	},

	onload(frm) {
		if (frm.is_new()) {
			setTimeout(() => {
				if (!frm.doc.size_chart_in_inch || frm.doc.size_chart_in_inch.length === 0) {
					frm.trigger('add_default_size_chart');
				}
			}, 500);
		}
	},

	add_default_size_chart(frm) {
		const sizes = ['36', '38', '40', '42'];
		sizes.forEach(size => {
			frm.add_child('size_chart_in_inch', {
				size_chart_in_inch: size
			});
		});
		frm.refresh_field('size_chart_in_inch');
	},

	fetch_tech_pack_data(frm) {
		if (!frm.doc.tech_pack_no) return;

		frappe.call({
			method: 'frappe.client.get',
			args: {
				doctype: 'Sketch Specification Sample Making Sheet',
				name: frm.doc.tech_pack_no
			},
			callback(r) {
				if (r.message) {
					let tech_pack = r.message;

					// Auto-populate Quality Inspection Template
					if (!frm.doc.link_nsnp) {
						frappe.db.get_list('Quality Inspection Template', { limit: 1 }).then(templates => {
							if (templates.length > 0) {
								frm.set_value('link_nsnp', templates[0].name);
							}
						});
					}

					// Auto-populate disclaimer
					if (!frm.doc.read_confirm_carefully) {
						frm.set_value('read_confirm_carefully', 'I confirm that all measurements, materials, and specifications have been reviewed and are accurate.');
					}

					// Set start time
					if (!frm.doc.start_time_date) {
						frm.set_value('start_time_date', frappe.datetime.now_datetime());
					}

					frappe.show_alert({ message: __('Tech Pack data fetched successfully'), indicator: 'green' });
				}
			}
		});
	}
});

frappe.ui.form.on("PPS Fabric Item", {
	actual_quantity: function (frm, cdt, cdn) {
		calculate_child_amount(frm, cdt, cdn);
	},
	rate: function (frm, cdt, cdn) {
		calculate_child_amount(frm, cdt, cdn);
	}
});

frappe.ui.form.on("PPS Trim Accessories Item", {
	actual_quantity: function (frm, cdt, cdn) {
		calculate_child_amount(frm, cdt, cdn);
	},
	rate: function (frm, cdt, cdn) {
		calculate_child_amount(frm, cdt, cdn);
	}
});

frappe.ui.form.on("Fabric Dupatta", {
	actual_quantity: function (frm, cdt, cdn) {
		calculate_child_amount(frm, cdt, cdn);
	},
	rate: function (frm, cdt, cdn) {
		calculate_child_amount(frm, cdt, cdn);
	}
});

function calculate_child_amount(frm, cdt, cdn) {
	let row = locals[cdt][cdn];
	let amount = (flt(row.actual_quantity) || 0) * (flt(row.rate) || 0);
	frappe.model.set_value(cdt, cdn, "amount", amount);
}
