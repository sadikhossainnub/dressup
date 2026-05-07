// Copyright (c) 2025, Prime Technology of Bangladesh and contributors
// For license information, please see license.txt

frappe.ui.form.on("Cost Estimation Accessory", {
	itemcode(frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		if (row.itemcode) {
			frappe.call({
				method: "erpnext.stock.utils.get_latest_stock_qty",
				args: { item_code: row.itemcode },
				callback(r) {
					frappe.model.set_value(cdt, cdn, "stock_in_hand", r.message || 0);
				}
			});
			frappe.db.get_value("Item Price", { item_code: row.itemcode }, "price_list_rate", (r) => {
				if (r && r.price_list_rate) {
					frappe.model.set_value(cdt, cdn, "rate", r.price_list_rate);
				} else {
					frappe.db.get_value("Item", row.itemcode, "valuation_rate", (r) => {
						frappe.model.set_value(cdt, cdn, "rate", r.valuation_rate || 0);
					});
				}
			});
		}
	},
	qty(frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		let amount = (flt(row.qty) * flt(row.rate));
		frappe.model.set_value(cdt, cdn, "amount", amount);
		frm.trigger("calculate_total_accessories");
	},
	rate(frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		let amount = (flt(row.qty) * flt(row.rate));
		frappe.model.set_value(cdt, cdn, "amount", amount);
		frm.trigger("calculate_total_accessories");
	},
	amount(frm) {
		frm.trigger("calculate_total_accessories");
	}
});

frappe.ui.form.on("Cost Estimation Material", {
	item_code(frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		if (row.item_code) {
			frappe.call({
				method: "erpnext.stock.utils.get_latest_stock_qty",
				args: { item_code: row.item_code },
				callback(r) {
					frappe.model.set_value(cdt, cdn, "stock_in_hand", r.message || 0);
				}
			});
			frappe.db.get_value("Item Price", { item_code: row.item_code }, "price_list_rate", (r) => {
				if (r && r.price_list_rate) {
					frappe.model.set_value(cdt, cdn, "rate", r.price_list_rate);
				} else {
					frappe.db.get_value("Item", row.item_code, "valuation_rate", (r) => {
						frappe.model.set_value(cdt, cdn, "rate", r.valuation_rate || 0);
					});
				}
			});
		}
	},
	qty(frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		let amount = (flt(row.qty) * flt(row.rate));
		frappe.model.set_value(cdt, cdn, "amount", amount);
		frm.trigger("calculate_total_fabric");
	},
	rate(frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		let amount = (flt(row.qty) * flt(row.rate));
		frappe.model.set_value(cdt, cdn, "amount", amount);
		frm.trigger("calculate_total_fabric");
	},
	amount(frm) {
		frm.trigger("calculate_total_fabric");
	}
});

frappe.ui.form.on("Cost Estimation", {
	refresh: function (frm) {
		let stock_status = frm.doc.stock_reservation_status;
		if (stock_status && frm.fields_dict.stock_reservation_status && frm.fields_dict.stock_reservation_status.$input) {
			let bg_color = "#f4f5f6";
			let text_color = "#1f272e";
			if (stock_status === "Reserved") {
				bg_color = "#e8f5e9";
				text_color = "#2e7d32";
			} else if (stock_status === "Partially Reserved") {
				bg_color = "#fff3e0";
				text_color = "#ef6c00";
			} else if (stock_status === "Unreserved") {
				bg_color = "#ffebee";
				text_color = "#c62828";
			}
			frm.fields_dict.stock_reservation_status.$input.css({
				"background-color": bg_color,
				"color": text_color,
				"font-weight": "bold"
			});
		}

		frm.set_query("tech_pack_no", () => {
			return {
				filters: {
					docstatus: 1
				}
			};
		});

		frm.set_query("warehouse", "materials", () => {
			return {
				filters: {
					company: frm.doc.company,
					is_group: 0
				}
			};
		});

		frm.set_query("warehouse", "accessories", () => {
			return {
				filters: {
					company: frm.doc.company,
					is_group: 0
				}
			};
		});

		if (frm.doc.docstatus === 1) {
			frappe.call({
				method: 'frappe.client.get_count',
				args: {
					doctype: 'Pre Production Sample',
					filters: { tech_pack_no: frm.doc.tech_pack_no }
				},
				callback: function (r) {
					if (!r.message || r.message === 0) {
						frm.add_custom_button(__('Pre Production Sample'), function () {
							frappe.model.open_mapped_doc({
								method: 'dressup.dressup.doctype.cost_estimation.cost_estimation.make_pre_production_sample',
								frm: frm
							});
						}, __('Create'));
					}
				}
			});

			frm.add_custom_button(__('Item'), function () {
				frappe.model.open_mapped_doc({
					method: 'dressup.dressup.doctype.cost_estimation.cost_estimation.make_item',
					frm: frm
				});
			}, __('Create'));
		}

		if (!frm.is_new() && frm.doc.docstatus === 0) {
			frm.add_custom_button(__('Request for Approval'), function () {
				frappe.call({
					method: 'dressup.dressup.doctype.cost_estimation.cost_estimation.trigger_request_for_approval',
					args: {
						docname: frm.doc.name
					},
					freeze: true,
					freeze_message: __('Sending Request...'),
					callback: function (r) {
						if (!r.exc) {
							frappe.msgprint(__('Request for Approval sent successfully.'));
						}
					}
				});
			});
		}
	},
	calculate_total_fabric(frm) {
		let total = 0;
		frm.doc.materials.forEach(row => {
			total += flt(row.amount);
		});
		frm.set_value("total_fabric", total);
	},
	calculate_total_accessories(frm) {
		let total = 0;
		frm.doc.accessories.forEach(row => {
			total += flt(row.amount);
		});
		frm.set_value("total_trim_and_accessories", total);
	},
	cutting_f(frm) { frm.trigger("calculate_total_tailoring"); },
	machine_embroidery_f(frm) { frm.trigger("calculate_total_tailoring"); },
	screen_print_f(frm) { frm.trigger("calculate_total_tailoring"); },
	sewing_f(frm) { frm.trigger("calculate_total_tailoring"); },
	hand_embroidery_f(frm) { frm.trigger("calculate_total_tailoring"); },
	block_print_f(frm) { frm.trigger("calculate_total_tailoring"); },
	hand_work_estimation(frm) { frm.trigger("calculate_total_tailoring"); },
	karchupi_f(frm) { frm.trigger("calculate_total_tailoring"); },
	tie_dye(frm) { frm.trigger("calculate_total_tailoring"); },
	calculate_total_tailoring(frm) {
		let total = flt(frm.doc.cutting_f) + flt(frm.doc.machine_embroidery_f) + flt(frm.doc.screen_print_f) +
			flt(frm.doc.sewing_f) + flt(frm.doc.hand_embroidery_f) + flt(frm.doc.block_print_f) +
			flt(frm.doc.hand_work_estimation) + flt(frm.doc.karchupi_f) + flt(frm.doc.tie_dye);
		frm.set_value("total_tailoring", total);
	},
	wash_iron(frm) { frm.trigger("calculate_total_finishing"); },
	qc_packaging(frm) { frm.trigger("calculate_total_finishing"); },
	transportation(frm) { frm.trigger("calculate_total_finishing"); },
	calculate_total_finishing(frm) {
		let total = flt(frm.doc.wash_iron) + flt(frm.doc.qc_packaging) + flt(frm.doc.transportation);
		frm.set_value("total_finishing", total);
	}
});
