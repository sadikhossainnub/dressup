// Copyright (c) 2025, Prime Technology of Bangladesh and contributors
// For license information, please see license.txt

frappe.ui.form.on("Pre Production Sample", {
	refresh(frm) {
		if (!frm.is_new() && frm.doc.docstatus === 0) {
			frappe.call({
				method: 'frappe.client.get_count',
				args: {
					doctype: 'Quality Inspection',
					filters: {
						reference_type: 'Pre Production Sample',
						reference_name: frm.doc.name
					}
				},
				callback: function (r) {
					if (!r.message || r.message === 0) {
						frm.add_custom_button(__('Quality Inspection'), function () {
							frappe.model.open_mapped_doc({
								method: 'dressup.dressup.doctype.pre_production_sample.pre_production_sample.make_quality_inspection',
								frm: frm
							});
						}, __('Create'));
					}
				}
			});
		}

		// Show Quality Inspection button for submitted PPS (for reference)
		if (frm.doc.docstatus === 1) {
			frm.add_custom_button(__('View Quality Inspection'), function () {
				frappe.set_route('List', 'Quality Inspection', {
					reference_type: 'Pre Production Sample',
					reference_name: frm.doc.name
				});
			});

			if (!frm.doc.sample_bom) {
				frm.add_custom_button(__('Sample BOM'), function() {
					create_bom(frm, "Sample Making");
				}, __('Create'));
			}

			if (!frm.doc.production_bom) {
				frm.add_custom_button(__('Production BOM'), function() {
					create_bom(frm, "Bulk Production");
				}, __('Create'));
			}

			if (frappe.user.has_role("Manufacturing Manager")) {
				frm.add_custom_button(__('Update Size Chart'), function() {
					frm.trigger('update_size_chart_dialog');
				});
			}
		}

		// Fetch from Cost Estimation button
		if (!frm.is_new() && frm.doc.cost_estimation) {
			frm.add_custom_button(__('Fetch from Cost Estimation'), function () {
				frappe.call({
					method: 'frappe.client.get',
					args: {
						doctype: 'Cost Estimation',
						name: frm.doc.cost_estimation,
						fields: ['designer', 'designer_name', 'design_no']
					},
					callback(r) {
						if (r.message) {
							let ce = r.message;
							frm.set_value('designer', ce.designer || '');
							frm.set_value('designer_name', ce.designer_name || '');
							frm.set_value('style_no', ce.design_no || '');
							frm.dirty();
							frappe.show_alert({
								message: __('Designer and Style No fetched from Cost Estimation'),
								indicator: 'green'
							});
						}
					}
				});
			}, __('Get'));
		}

		// Add Full Tech Pack Print Button
		if (!frm.is_new()) {
			frm.add_custom_button(__('Print Master Tech Pack'), function () {
				frappe.utils.print(frm.doc.doctype, frm.doc.name, "Full Tech Pack");
			}, __('Print'));
		}
	},

	before_submit(frm) {
		// Check if Quality Inspection exists and is accepted
		return frappe.call({
			method: 'frappe.client.get_list',
			args: {
				doctype: 'Quality Inspection',
				filters: {
					reference_type: 'Pre Production Sample',
					reference_name: frm.doc.name,
					docstatus: 1
				},
				fields: ['name', 'status']
			},
			async: false,
			callback: function (r) {
				if (!r.message || r.message.length === 0) {
					frappe.throw(__('Please create and submit Quality Inspection before submitting PPS'));
					frappe.validated = false;
				} else {
					let qi = r.message[0];
					if (qi.status !== 'Accepted') {
						frappe.throw(__('Quality Inspection must be Accepted before submitting PPS. Current status: {0}', [qi.status]));
						frappe.validated = false;
					}
				}
			}
		});
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

			if (!frm.doc.link_nsnp) {
				frappe.db.get_single_value("Dressup Settings", "default_pps_inspection").then(value => {
					if (value) {
						frm.set_value("link_nsnp", value);
					}
				});
			}
		}
	},

	add_default_size_chart(frm) {
		const sizes = ['36', '38', '40', '42', '44'];
		const existing_sizes = new Set((frm.doc.size_chart_in_inch || []).map((row) => row.size_chart_in_inch));
		sizes.forEach(size => {
			if (!existing_sizes.has(size)) {
				frm.add_child('size_chart_in_inch', {
					size_chart_in_inch: size
				});
			}
		});
		frm.refresh_field('size_chart_in_inch');
	},

	fetch_tech_pack_data(frm) {
		if (!frm.doc.tech_pack_no) return;

		frappe.call({
			method: 'frappe.client.get',
			args: {
				doctype: 'Sketch Specification',
				name: frm.doc.tech_pack_no
			},
			callback(r) {
				if (r.message) {
					let tech_pack = r.message;

					// Auto-populate Quality Inspection Template
					if (!frm.doc.link_nsnp) {
						frappe.db.get_single_value("Dressup Settings", "default_pps_inspection").then(value => {
							if (value) {
								frm.set_value('link_nsnp', value);
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

					// Set style fields
					if (tech_pack.bottom_waist) frm.set_value('bottom_waist', tech_pack.bottom_waist);
					if (tech_pack.bottom_style) frm.set_value('bottom_style', tech_pack.bottom_style);
					if (tech_pack.sleeve) frm.set_value('sleeve', tech_pack.sleeve);

					frappe.show_alert({ message: __('Tech Pack data fetched successfully'), indicator: 'green' });
				}
			}
		});
	},

	pattern_variation: function(frm) { calculate_suggested_selling_prices(frm); },
	screen_print_machine_emb_65: function(frm) { calculate_suggested_selling_prices(frm); },
	hand_embroidery_75: function(frm) { calculate_suggested_selling_prices(frm); },
	cutting_f: function(frm) { frm.trigger("calculate_total_tailoring"); },
	sewing_f: function(frm) { frm.trigger("calculate_total_tailoring"); },
	hand_work_estimation: function(frm) { frm.trigger("calculate_total_tailoring"); },
	machine_embroidery_f: function(frm) { frm.trigger("calculate_total_tailoring"); },
	hand_embroidery_f: function(frm) { frm.trigger("calculate_total_tailoring"); },
	karchupi_f: function(frm) { frm.trigger("calculate_total_tailoring"); },
	screen_print_f: function(frm) { frm.trigger("calculate_total_tailoring"); },
	block_print_f: function(frm) { frm.trigger("calculate_total_tailoring"); },
	tie_dye: function(frm) { frm.trigger("calculate_total_tailoring"); },
	wash_iron: function(frm) { frm.trigger("calculate_total_finishing"); },
	qc_packaging: function(frm) { frm.trigger("calculate_total_finishing"); },
	transportation: function(frm) { frm.trigger("calculate_total_finishing"); },
	fusingandpasting: function(frm) { frm.trigger("calculate_total_finishing"); },
	others: function(frm) { frm.trigger("calculate_total_finishing"); },

	calculate_total_tailoring: function(frm) {
		let total = flt(frm.doc.cutting_f) + flt(frm.doc.sewing_f) + flt(frm.doc.hand_work_estimation) +
					flt(frm.doc.machine_embroidery_f) + flt(frm.doc.hand_embroidery_f) + flt(frm.doc.karchupi_f) +
					flt(frm.doc.screen_print_f) + flt(frm.doc.block_print_f) + flt(frm.doc.tie_dye);
		frm.set_value("total_tailoring", total);
		calculate_suggested_selling_prices(frm);
	},

	calculate_total_finishing: function(frm) {
		let total = flt(frm.doc.wash_iron) + flt(frm.doc.qc_packaging) + flt(frm.doc.transportation) + flt(frm.doc.fusingandpasting) + flt(frm.doc.others);
		frm.set_value("total_finishing", total);
		calculate_suggested_selling_prices(frm);
	},

	update_size_chart_dialog: function(frm) {
		const dialog = new frappe.ui.Dialog({
			title: __("Update Size Chart"),
			size: "extra-large",
			fields: [
				{
					fieldname: "size_chart",
					fieldtype: "Table",
					label: __("Size Chart in Inch"),
					allow_bulk_edit: true,
					cannot_add_rows: false,
					cannot_delete_rows: false,
					data: (frm.doc.size_chart_in_inch || []).map(d => ({
						docname: d.name,
						size_chart_in_inch: d.size_chart_in_inch,
						production_qty: d.production_qty,
						color: d.color,
						length: d.length,
						neck: d.neck,
						waist: d.waist,
						sleeve: d.sleeve,
						sleeve_opening: d.sleeve_opening,
						bottom_length: d.bottom_length,
						bottom_waist: d.bottom_waist,
						bottom_thigh: d.bottom_thigh,
						bottom_crotch: d.bottom_crotch,
						leg_opening: d.leg_opening,
						shrug_koti_length: d.shrug_koti_length,
						koti_sleeve: d.koti_sleeve,
						koti_sleeve_opening: d.koti_sleeve_opening,
						others1: d.others1
					})),
					fields: [
						{
							fieldname: "docname",
							fieldtype: "Data",
							label: __("Docname"),
							read_only: 1,
							hidden: 1
						},
						{
							fieldname: "size_chart_in_inch",
							fieldtype: "Select",
							label: __("Size"),
							options: "\n32\n34\n36\n38\n40\n42\n44\n46\n48\n50\nunstitch",
							reqd: 1,
							in_list_view: 1
						},
						{
							fieldname: "production_qty",
							fieldtype: "Int",
							label: __("Production Qty"),
							in_list_view: 1
						},
						{
							fieldname: "color",
							fieldtype: "Link",
							label: __("Color"),
							options: "Color",
							in_list_view: 1
						},
						{
							fieldname: "length",
							fieldtype: "Data",
							label: __("Length (Body)"),
							in_list_view: 1
						},
						{
							fieldname: "neck",
							fieldtype: "Data",
							label: __("Neck"),
							in_list_view: 1
						},
						{
							fieldname: "waist",
							fieldtype: "Data",
							label: __("Waist (Body)"),
							in_list_view: 1
						},
						{
							fieldname: "sleeve",
							fieldtype: "Data",
							label: __("Sleeve"),
							in_list_view: 1
						},
						{
							fieldname: "sleeve_opening",
							fieldtype: "Data",
							label: __("Sleeve Opening"),
							in_list_view: 1
						},
						{
							fieldname: "bottom_length",
							fieldtype: "Data",
							label: __("Bottom Length"),
							in_list_view: 1
						},
						{
							fieldname: "bottom_waist",
							fieldtype: "Data",
							label: __("Bottom Waist"),
							in_list_view: 1
						},
						{
							fieldname: "bottom_thigh",
							fieldtype: "Data",
							label: __("Bottom Thigh"),
							in_list_view: 1
						},
						{
							fieldname: "bottom_crotch",
							fieldtype: "Data",
							label: __("Bottom Crotch"),
							in_list_view: 1
						},
						{
							fieldname: "leg_opening",
							fieldtype: "Data",
							label: __("Leg Opening"),
							in_list_view: 1
						},
						{
							fieldname: "shrug_koti_length",
							fieldtype: "Data",
							label: __("Shrug/ Koti Length"),
							in_list_view: 1
						},
						{
							fieldname: "koti_sleeve",
							fieldtype: "Data",
							label: __("Koti Sleeve"),
							in_list_view: 1
						},
						{
							fieldname: "koti_sleeve_opening",
							fieldtype: "Data",
							label: __("Koti/ Sleeve Opening"),
							in_list_view: 1
						},
						{
							fieldname: "others1",
							fieldtype: "Data",
							label: __("Others"),
							in_list_view: 1
						}
					]
				}
			],
			primary_action_label: __("Update"),
			primary_action: () => {
				let size_chart_data = dialog.fields_dict.size_chart.df.data || [];
				frappe.call({
					method: "dressup.dressup.doctype.pre_production_sample.pre_production_sample.update_submitted_size_chart",
					args: {
						docname: frm.doc.name,
						size_chart: size_chart_data.map(d => ({
							size_chart_in_inch: d.size_chart_in_inch,
							production_qty: d.production_qty,
							color: d.color,
							length: d.length,
							neck: d.neck,
							waist: d.waist,
							sleeve: d.sleeve,
							sleeve_opening: d.sleeve_opening,
							bottom_length: d.bottom_length,
							bottom_waist: d.bottom_waist,
							bottom_thigh: d.bottom_thigh,
							bottom_crotch: d.bottom_crotch,
							leg_opening: d.leg_opening,
							shrug_koti_length: d.shrug_koti_length,
							koti_sleeve: d.koti_sleeve,
							koti_sleeve_opening: d.koti_sleeve_opening,
							others1: d.others1
						}))
					},
					freeze: true,
					freeze_message: __("Updating Size Chart..."),
					callback: (r) => {
						frm.reload_doc();
						dialog.hide();
					}
				});
			}
		});
		dialog.show();
	},
});


frappe.ui.form.on("PPS Fabric Item", {
	item_code: function(frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		if (row.item_code) {
			frappe.call({
				method: "erpnext.stock.utils.get_latest_stock_qty",
				args: { item_code: row.item_code },
				callback(r) {
					frappe.model.set_value(cdt, cdn, "stock_in_hand", r.message || 0);
				}
			});
			// Fetch all item attributes
			frappe.call({
				method: "frappe.client.get",
				args: { doctype: "Item", name: row.item_code, fields: ["attributes"] },
				callback(r) {
					if (r.message && r.message.attributes && r.message.attributes.length) {
						let attrs = r.message.attributes.map(a => a.attribute + ": " + (a.attribute_value || ""));
						frappe.model.set_value(cdt, cdn, "item_attributes", attrs.join(", "));
					} else {
						frappe.model.set_value(cdt, cdn, "item_attributes", "");
					}
				}
			});
			frappe.db.get_value("Item Price", { item_code: row.item_code, buying: 1 }, "price_list_rate", (r) => {
				if (r && r.price_list_rate) {
					frappe.model.set_value(cdt, cdn, "rate", r.price_list_rate);
				} else {
					frappe.db.get_value("Item", row.item_code, ["last_purchase_rate", "valuation_rate", "standard_rate"], (res) => {
						let final_rate = 0;
						if (res) {
							final_rate = res.last_purchase_rate || res.valuation_rate || res.standard_rate || 0;
						}
						frappe.model.set_value(cdt, cdn, "rate", final_rate);
					});
				}
			});
		}
	},
	actual_quantity: function (frm, cdt, cdn) {
		calculate_child_amount(frm, cdt, cdn);
		calculate_total_fabrics(frm);
	},
	rate: function (frm, cdt, cdn) {
		calculate_child_amount(frm, cdt, cdn);
		calculate_total_fabrics(frm);
	},
	fabrics_remove: function (frm) {
		calculate_total_fabrics(frm);
	}
});

frappe.ui.form.on("PPS Trim Accessories Item", {
	item_code: function(frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		if (row.item_code) {
			frappe.call({
				method: "erpnext.stock.utils.get_latest_stock_qty",
				args: { item_code: row.item_code },
				callback(r) {
					frappe.model.set_value(cdt, cdn, "stock_in_hand", r.message || 0);
				}
			});
			// Fetch all item attributes
			frappe.call({
				method: "frappe.client.get",
				args: { doctype: "Item", name: row.item_code, fields: ["attributes"] },
				callback(r) {
					if (r.message && r.message.attributes && r.message.attributes.length) {
						let attrs = r.message.attributes.map(a => a.attribute + ": " + (a.attribute_value || ""));
						frappe.model.set_value(cdt, cdn, "item_attributes", attrs.join(", "));
					} else {
						frappe.model.set_value(cdt, cdn, "item_attributes", "");
					}
				}
			});
			frappe.db.get_value("Item Price", { item_code: row.item_code, buying: 1 }, "price_list_rate", (r) => {
				if (r && r.price_list_rate) {
					frappe.model.set_value(cdt, cdn, "rate", r.price_list_rate);
				} else {
					frappe.db.get_value("Item", row.item_code, ["last_purchase_rate", "valuation_rate", "standard_rate"], (res) => {
						let final_rate = 0;
						if (res) {
							final_rate = res.last_purchase_rate || res.valuation_rate || res.standard_rate || 0;
						}
						frappe.model.set_value(cdt, cdn, "rate", final_rate);
					});
				}
			});
		}
	},
	actual_quantity: function (frm, cdt, cdn) {
		calculate_child_amount(frm, cdt, cdn);
		calculate_total_trim_accessories(frm);
	},
	rate: function (frm, cdt, cdn) {
		calculate_child_amount(frm, cdt, cdn);
		calculate_total_trim_accessories(frm);
	},
	trim_accessories_remove: function (frm) {
		calculate_total_trim_accessories(frm);
	}
});

frappe.ui.form.on("Fabric Dupatta", {
	item_code: function(frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		if (row.item_code) {
			frappe.call({
				method: "erpnext.stock.utils.get_latest_stock_qty",
				args: { item_code: row.item_code },
				callback(r) {
					frappe.model.set_value(cdt, cdn, "stock_in_hand", r.message || 0);
				}
			});
			// Fetch all item attributes
			frappe.call({
				method: "frappe.client.get",
				args: { doctype: "Item", name: row.item_code, fields: ["attributes"] },
				callback(r) {
					if (r.message && r.message.attributes && r.message.attributes.length) {
						let attrs = r.message.attributes.map(a => a.attribute + ": " + (a.attribute_value || ""));
						frappe.model.set_value(cdt, cdn, "item_attributes", attrs.join(", "));
					} else {
						frappe.model.set_value(cdt, cdn, "item_attributes", "");
					}
				}
			});
			frappe.db.get_value("Item Price", { item_code: row.item_code, buying: 1 }, "price_list_rate", (r) => {
				if (r && r.price_list_rate) {
					frappe.model.set_value(cdt, cdn, "rate", r.price_list_rate);
				} else {
					frappe.db.get_value("Item", row.item_code, ["last_purchase_rate", "valuation_rate", "standard_rate"], (res) => {
						let final_rate = 0;
						if (res) {
							final_rate = res.last_purchase_rate || res.valuation_rate || res.standard_rate || 0;
						}
						frappe.model.set_value(cdt, cdn, "rate", final_rate);
					});
				}
			});
		}
	},
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

function calculate_total_fabrics(frm) {
	let total = 0;
	(frm.doc.fabrics || []).forEach(row => {
		total += flt(row.amount) || 0;
	});
	frm.set_value("total_fabrics", total);
	calculate_suggested_selling_prices(frm);
}

function calculate_total_trim_accessories(frm) {
	let total = 0;
	(frm.doc.trim_accessories || []).forEach(row => {
		total += flt(row.amount) || 0;
	});
	frm.set_value("total_trim_accessories", total);
	calculate_suggested_selling_prices(frm);
}

frappe.ui.form.on("Size Chart in Inch", {
	production_qty: function (frm) {
		calculate_total_production_qty(frm);
	},
	size_chart_in_inch_remove: function (frm) {
		calculate_total_production_qty(frm);
	}
});

function calculate_total_production_qty(frm) {
	let total = 0;
	(frm.doc.size_chart_in_inch || []).forEach(row => {
		total += cint(row.production_qty) || 0;
	});
	frm.set_value("total_production_qty", total);
}

function calculate_suggested_selling_prices(frm) {
	let total_cost = flt(frm.doc.total_fabrics) + flt(frm.doc.total_trim_accessories) + 
					 flt(frm.doc.total_tailoring) + flt(frm.doc.total_finishing);
	
	if (flt(frm.doc.screen_print_machine_emb_65)) {
		frm.set_value("screen_print_machine_emb_only", total_cost * (1 + flt(frm.doc.screen_print_machine_emb_65) / 100));
	} else {
		frm.set_value("screen_print_machine_emb_only", 0);
	}

	if (flt(frm.doc.pattern_variation)) {
		frm.set_value("for_pattern_variation_only", total_cost * (1 + flt(frm.doc.pattern_variation) / 100));
	} else {
		frm.set_value("for_pattern_variation_only", 0);
	}

	if (flt(frm.doc.hand_embroidery_75)) {
		frm.set_value("hand_embroidery_only", total_cost * (1 + flt(frm.doc.hand_embroidery_75) / 100));
	} else {
		frm.set_value("hand_embroidery_only", 0);
	}
}

function create_bom(frm, bom_type) {
	frappe.call({
		method: 'dressup.dressup.doctype.pre_production_sample.pre_production_sample.make_bom',
		args: { source_name: frm.doc.name, bom_type: bom_type },
		callback: function(r) {
			if (r.message) {
				frappe.set_route('Form', 'BOM', r.message);
			}
		}
	});
}
