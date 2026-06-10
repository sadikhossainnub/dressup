// Copyright (c) 2025, Prime Technology of Bangladesh and contributors
// For license information, please see license.txt

frappe.ui.form.on("Cost Estimation Accessory", {
	itemcode(frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		if (row.itemcode) {
			frappe.call({
				method: "frappe.client.get_list",
				args: {
					doctype: "Bin",
					filters: { item_code: row.itemcode },
					fields: ["actual_qty"]
				},
				callback(r) {
					let total_qty = 0;
					if (r.message) {
						r.message.forEach(bin => {
							total_qty += (bin.actual_qty || 0);
						});
					}
					frappe.model.set_value(cdt, cdn, "stock_in_hand", total_qty);
				}
			});
			// Fetch all item attributes
			frappe.call({
				method: "frappe.client.get",
				args: { doctype: "Item", name: row.itemcode, fields: ["attributes"] },
				callback(r) {
					if (r.message && r.message.attributes && r.message.attributes.length) {
						let attrs = r.message.attributes.map(a => a.attribute + ": " + (a.attribute_value || ""));
						frappe.model.set_value(cdt, cdn, "item_attributes", attrs.join(", "));
					} else {
						frappe.model.set_value(cdt, cdn, "item_attributes", "");
					}
				}
			});
			frappe.db.get_value("Item Price", { item_code: row.itemcode, buying: 1 }, "price_list_rate", (r) => {
				if (r && r.price_list_rate) {
					frappe.model.set_value(cdt, cdn, "rate", r.price_list_rate);
				} else {
					frappe.db.get_value("Item", row.itemcode, ["last_purchase_rate", "valuation_rate", "standard_rate"], (res) => {
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
				method: "frappe.client.get_list",
				args: {
					doctype: "Bin",
					filters: { item_code: row.item_code },
					fields: ["actual_qty"]
				},
				callback(r) {
					let total_qty = 0;
					if (r.message) {
						r.message.forEach(bin => {
							total_qty += (bin.actual_qty || 0);
						});
					}
					frappe.model.set_value(cdt, cdn, "stock_in_hand", total_qty);
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

			if (frm.has_perm("write")) {
				frm.add_custom_button(__("Update Items"), () => {
					frm.trigger("update_items_dialog");
				});
			}

			// Stock Reservation button group
			let has_unreserved_stock = false;
			(frm.doc.materials || []).forEach(row => {
				if (flt(row.qty) > flt(row.reserved_qty) && row.item_code && row.warehouse) {
					has_unreserved_stock = true;
				}
			});
			(frm.doc.accessories || []).forEach(row => {
				if (flt(row.qty) > flt(row.reserved_qty) && row.itemcode && row.warehouse) {
					has_unreserved_stock = true;
				}
			});

			let has_reserved_stock = false;
			(frm.doc.materials || []).forEach(row => {
				if (flt(row.reserved_qty) > 0) {
					has_reserved_stock = true;
				}
			});
			(frm.doc.accessories || []).forEach(row => {
				if (flt(row.reserved_qty) > 0) {
					has_reserved_stock = true;
				}
			});

			if (has_unreserved_stock) {
				frm.add_custom_button(
					__("Reserve"),
					() => frm.trigger("create_stock_reservation_entries"),
					__("Stock Reservation")
				);
			}

			if (has_reserved_stock) {
				frm.add_custom_button(
					__("Unreserve"),
					() => frm.trigger("cancel_stock_reservation_entries"),
					__("Stock Reservation")
				);

				frm.add_custom_button(
					__("Reserved Stock"),
					() => frm.trigger("show_reserved_stock"),
					__("Stock Reservation")
				);
			}
		}
	},

	create_stock_reservation_entries: function (frm) {
		const dialog = new frappe.ui.Dialog({
			title: __("Stock Reservation"),
			size: "extra-large",
			fields: [
				{
					fieldname: "items",
					fieldtype: "Table",
					label: __("Items to Reserve"),
					allow_bulk_edit: false,
					cannot_add_rows: true,
					cannot_delete_rows: true,
					data: [],
					fields: [
						{
							fieldname: "row_id",
							fieldtype: "Data",
							label: __("Row ID"),
							read_only: 1,
							hidden: 1
						},
						{
							fieldname: "child_doctype",
							fieldtype: "Data",
							label: __("Child Doctype"),
							read_only: 1,
							hidden: 1
						},
						{
							fieldname: "item_code",
							fieldtype: "Link",
							label: __("Item Code"),
							options: "Item",
							reqd: 1,
							read_only: 1,
							in_list_view: 1,
						},
						{
							fieldname: "warehouse",
							fieldtype: "Link",
							label: __("Warehouse"),
							options: "Warehouse",
							reqd: 1,
							in_list_view: 1,
							get_query: () => {
								return {
									filters: [["Warehouse", "is_group", "!=", 1]],
								};
							},
						},
						{
							fieldname: "qty_to_reserve",
							fieldtype: "Float",
							label: __("Qty"),
							reqd: 1,
							in_list_view: 1,
						},
					],
				},
			],
			primary_action_label: __("Reserve Stock"),
			primary_action: () => {
				var selected_items = dialog.fields_dict.items.grid.get_selected_children();

				if (selected_items && selected_items.length > 0) {
					frappe.call({
						method: "dressup.dressup.doctype.cost_estimation.cost_estimation.create_stock_reservation_entries_via_dialog",
						args: {
							docname: frm.doc.name,
							items_details: selected_items.map(d => ({
								row_id: d.row_id,
								child_doctype: d.child_doctype,
								item_code: d.item_code,
								warehouse: d.warehouse,
								qty_to_reserve: d.qty_to_reserve
							}))
						},
						freeze: true,
						freeze_message: __("Reserving Stock..."),
						callback: (r) => {
							frm.reload_doc();
						},
					});

					dialog.hide();
				} else {
					frappe.msgprint(__("Please select items to reserve."));
				}
			},
		});

		(frm.doc.materials || []).forEach((item) => {
			let unreserved_qty = flt(item.qty) - flt(item.reserved_qty);
			if (unreserved_qty > 0 && item.item_code && item.warehouse) {
				dialog.fields_dict.items.df.data.push({
					__checked: 1,
					row_id: item.name,
					child_doctype: "Cost Estimation Material",
					item_code: item.item_code,
					warehouse: item.warehouse,
					qty_to_reserve: unreserved_qty,
				});
			}
		});

		(frm.doc.accessories || []).forEach((item) => {
			let unreserved_qty = flt(item.qty) - flt(item.reserved_qty);
			if (unreserved_qty > 0 && item.itemcode && item.warehouse) {
				dialog.fields_dict.items.df.data.push({
					__checked: 1,
					row_id: item.name,
					child_doctype: "Cost Estimation Accessory",
					item_code: item.itemcode,
					warehouse: item.warehouse,
					qty_to_reserve: unreserved_qty,
				});
			}
		});

		dialog.fields_dict.items.grid.refresh();
		dialog.show();
	},

	cancel_stock_reservation_entries: function (frm) {
		const dialog = new frappe.ui.Dialog({
			title: __("Stock Unreservation"),
			size: "extra-large",
			fields: [
				{
					fieldname: "sr_entries",
					fieldtype: "Table",
					label: __("Reserved Stock"),
					allow_bulk_edit: false,
					cannot_add_rows: true,
					cannot_delete_rows: true,
					in_place_edit: true,
					data: [],
					fields: [
						{
							fieldname: "sre",
							fieldtype: "Link",
							label: __("Stock Reservation Entry"),
							options: "Stock Reservation Entry",
							reqd: 1,
							read_only: 1,
							in_list_view: 1,
						},
						{
							fieldname: "item_code",
							fieldtype: "Link",
							label: __("Item Code"),
							options: "Item",
							reqd: 1,
							read_only: 1,
							in_list_view: 1,
						},
						{
							fieldname: "warehouse",
							fieldtype: "Link",
							label: __("Warehouse"),
							options: "Warehouse",
							reqd: 1,
							read_only: 1,
							in_list_view: 1,
						},
						{
							fieldname: "qty",
							fieldtype: "Float",
							label: __("Qty"),
							reqd: 1,
							read_only: 1,
							in_list_view: 1,
						},
					],
				},
			],
			primary_action_label: __("Unreserve Stock"),
			primary_action: () => {
				var selected_entries = dialog.fields_dict.sr_entries.grid.get_selected_children();

				if (selected_entries && selected_entries.length > 0) {
					frappe.call({
						method: "dressup.dressup.doctype.cost_estimation.cost_estimation.cancel_stock_reservation_entries_via_dialog",
						args: {
							docname: frm.doc.name,
							sre_list: selected_entries.map((item) => item.sre),
						},
						freeze: true,
						freeze_message: __("Unreserving Stock..."),
						callback: (r) => {
							frm.reload_doc();
						},
					});

					dialog.hide();
				} else {
					frappe.msgprint(__("Please select items to unreserve."));
				}
			},
		});

		frappe.call({
			method: "erpnext.stock.doctype.stock_reservation_entry.stock_reservation_entry.get_stock_reservation_entries_for_voucher",
			args: {
				voucher_type: frm.doctype,
				voucher_no: frm.docname,
			},
			callback: (r) => {
				if (!r.exc && r.message) {
					r.message.forEach((sre) => {
						if (flt(sre.reserved_qty) > flt(sre.delivered_qty)) {
							dialog.fields_dict.sr_entries.df.data.push({
								sre: sre.name,
								item_code: sre.item_code,
								warehouse: sre.warehouse,
								qty: flt(sre.reserved_qty) - flt(sre.delivered_qty),
							});
						}
					});
				}
			},
		}).then(() => {
			dialog.fields_dict.sr_entries.grid.refresh();
			dialog.show();
		});
	},

	show_reserved_stock: function (frm) {
		frappe.route_options = {
			company: frm.doc.company,
			voucher_type: frm.doctype,
			voucher_no: frm.docname,
		};
		frappe.set_route("query-report", "Reserved Stock");
	},

	update_items_dialog: function (frm) {
		const dialog = new frappe.ui.Dialog({
			title: __("Update Items (Materials & Accessories)"),
			size: "extra-large",
			fields: [
				{
					fieldname: "materials",
					fieldtype: "Table",
					label: __("Materials"),
					allow_bulk_edit: false,
					cannot_add_rows: true,
					cannot_delete_rows: true,
					data: (frm.doc.materials || []).map(d => ({
						docname: d.name,
						item_code: d.item_code,
						warehouse: d.warehouse,
						qty: d.qty,
						rate: d.rate
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
							fieldname: "item_code",
							fieldtype: "Link",
							label: __("Item Code"),
							options: "Item",
							read_only: 1,
							in_list_view: 1
						},
						{
							fieldname: "warehouse",
							fieldtype: "Link",
							label: __("Warehouse"),
							options: "Warehouse",
							in_list_view: 1,
							get_query: () => {
								return {
									filters: [["Warehouse", "is_group", "!=", 1]],
								};
							},
						},
						{
							fieldname: "qty",
							fieldtype: "Float",
							label: __("Qty"),
							in_list_view: 1
						},
						{
							fieldname: "rate",
							fieldtype: "Currency",
							label: __("Rate"),
							in_list_view: 1
						}
					]
				},
				{
					fieldname: "sec_break",
					fieldtype: "Section Break"
				},
				{
					fieldname: "accessories",
					fieldtype: "Table",
					label: __("Trim & Accessories"),
					allow_bulk_edit: false,
					cannot_add_rows: true,
					cannot_delete_rows: true,
					data: (frm.doc.accessories || []).map(d => ({
						docname: d.name,
						itemcode: d.itemcode,
						warehouse: d.warehouse,
						qty: d.qty,
						rate: d.rate
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
							fieldname: "itemcode",
							fieldtype: "Link",
							label: __("Item Code"),
							options: "Item",
							read_only: 1,
							in_list_view: 1
						},
						{
							fieldname: "warehouse",
							fieldtype: "Link",
							label: __("Warehouse"),
							options: "Warehouse",
							in_list_view: 1,
							get_query: () => {
								return {
									filters: [["Warehouse", "is_group", "!=", 1]],
								};
							},
						},
						{
							fieldname: "qty",
							fieldtype: "Float",
							label: __("Qty"),
							in_list_view: 1
						},
						{
							fieldname: "rate",
							fieldtype: "Currency",
							label: __("Rate"),
							in_list_view: 1
						}
					]
				}
			],
			primary_action_label: __("Update"),
			primary_action: () => {
				let materials_data = dialog.fields_dict.materials.df.data || [];
				let accessories_data = dialog.fields_dict.accessories.df.data || [];

				let has_reserved_stock = false;
				(frm.doc.materials || []).forEach(row => {
					if (flt(row.reserved_qty) > 0) has_reserved_stock = true;
				});
				(frm.doc.accessories || []).forEach(row => {
					if (flt(row.reserved_qty) > 0) has_reserved_stock = true;
				});

				const perform_update = () => {
					frappe.call({
						method: "dressup.dressup.doctype.cost_estimation.cost_estimation.update_submitted_items",
						args: {
							docname: frm.doc.name,
							materials: materials_data.map(d => ({
								docname: d.docname,
								warehouse: d.warehouse,
								qty: d.qty,
								rate: d.rate
							})),
							accessories: accessories_data.map(d => ({
								docname: d.docname,
								warehouse: d.warehouse,
								qty: d.qty,
								rate: d.rate
							}))
						},
						freeze: true,
						freeze_message: __("Updating Items..."),
						callback: (r) => {
							frm.reload_doc();
						}
					});
					dialog.hide();
				};

				if (has_reserved_stock) {
					frappe.confirm(
						__("Updating quantities/warehouses will cancel and release all existing stock reservations for this document. Are you sure you want to proceed?"),
						() => {
							perform_update();
						}
					);
				} else {
					perform_update();
				}
			}
		});

		dialog.show();
	},

	calculate_total_fabric(frm) {
		let total = 0;
		frm.doc.materials.forEach(row => {
			total += flt(row.amount);
		});
		frm.set_value("total_fabric", total);
		calculate_suggested_selling_prices(frm);
	},
	calculate_total_accessories(frm) {
		let total = 0;
		frm.doc.accessories.forEach(row => {
			total += flt(row.amount);
		});
		frm.set_value("total_trim_and_accessories", total);
		calculate_suggested_selling_prices(frm);
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
		calculate_suggested_selling_prices(frm);
	},
	wash_iron(frm) { frm.trigger("calculate_total_finishing"); },
	qc_packaging(frm) { frm.trigger("calculate_total_finishing"); },
	transportation(frm) { frm.trigger("calculate_total_finishing"); },
	fusingandpasting(frm) { frm.trigger("calculate_total_finishing"); },
	others(frm) { frm.trigger("calculate_total_finishing"); },
	calculate_total_finishing(frm) {
		let total = flt(frm.doc.wash_iron) + flt(frm.doc.qc_packaging) + flt(frm.doc.transportation) + flt(frm.doc.fusingandpasting) + flt(frm.doc.others);
		frm.set_value("total_finishing", total);
		calculate_suggested_selling_prices(frm);
	},
	pattern_variation: function(frm) { calculate_suggested_selling_prices(frm); },
	screen_print_machine_emb_65: function(frm) { calculate_suggested_selling_prices(frm); },
	hand_embroidery_75: function(frm) { calculate_suggested_selling_prices(frm); },
	source_warehouse: function(frm) {
		if (frm.doc.source_warehouse) {
			if (frm.doc.materials) {
				frm.doc.materials.forEach(row => {
					frappe.model.set_value(row.doctype, row.name, "warehouse", frm.doc.source_warehouse);
				});
			}
			if (frm.doc.accessories) {
				frm.doc.accessories.forEach(row => {
					frappe.model.set_value(row.doctype, row.name, "warehouse", frm.doc.source_warehouse);
				});
			}
		}
	},
});

function calculate_suggested_selling_prices(frm) {
	let total_cost = flt(frm.doc.total_fabric) + flt(frm.doc.total_trim_and_accessories) + 
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

