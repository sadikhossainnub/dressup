// Copyright (c) 2025, Prime Technology of Bangladesh and contributors
// For license information, please see license.txt

frappe.ui.form.on("Cost Estimation Accessory", {
	itemcode(frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		if (row.itemcode) {
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
	refresh(frm) {
		frm.set_query("tech_pack_no", () => {
			return {
				filters: {
					docstatus: 1
				}
			};
		});

		if (frm.doc.docstatus === 1) {
			frappe.db.count('Pre Production Sample', { tech_pack_no: frm.doc.tech_pack_no }).then(count => {
				if (count === 0) {
					frm.add_custom_button(__('Pre Production Sample'), function () {
						frappe.model.open_mapped_doc({
							method: 'dressup.dressup.doctype.cost_estimation.cost_estimation.make_pre_production_sample',
							frm: frm
						});
					}, __('Create'));
				}
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
