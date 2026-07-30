/**
 * Override for erpnext.utils.update_child_items
 *
 * Adds "Discount %" and "Discount Amount" columns to the "Update Items" dialog.
 *
 * Design notes:
 *   - price_list_rate is the anchor. All discount ↔ rate calculations are based on it.
 *   - Pricing Rule discounts: when a new item is selected, get_item_details returns
 *     `rate` (Pricing Rule applied), `price_list_rate`, `discount_percentage`, and
 *     `discount_amount` — all are populated into the row so the dialog shows the
 *     correct Pricing Rule values immediately.
 *   - For existing rows, frm.doc.items already has these fields stored on save,
 *     so they pre-populate correctly.
 *   - Editing discount_percentage → rate and discount_amount recalculate.
 *   - Editing discount_amount   → rate and discount_percentage recalculate.
 *   - Editing rate directly     → discount_percentage and discount_amount recalculate.
 *   - When price_list_rate is 0 (e.g. item has no price list entry), discount
 *     fields are shown but cross-calculation is skipped with a toast warning.
 *   - When rate > price_list_rate (margin scenario), discount % is shown as 0
 *     (the server will apply margin logic on save).
 *   - Server-side update_child_qty_rate does NOT read discount fields from payload;
 *     it derives them from price_list_rate vs rate — so sending adjusted `rate`
 *     is sufficient. No server-side patch required.
 */

frappe.provide("erpnext.utils");

erpnext.utils.update_child_items = function (opts) {
	const frm = opts.frm;
	const cannot_add_row =
		typeof opts.cannot_add_row === "undefined" ? true : opts.cannot_add_row;
	const child_docname =
		typeof opts.child_docname === "undefined" ? "items" : opts.child_docname;
	const child_meta = frappe.get_meta(`${frm.doc.doctype} Item`);
	const has_reserved_stock = opts.has_reserved_stock ? true : false;

	// Resolve field precision from child doctype meta; fallback to 2
	const get_precision = (fieldname) => {
		const f = child_meta.fields.find((f) => f.fieldname === fieldname);
		return (f && f.precision != null) ? f.precision : 2;
	};

	// ------------------------------------------------------------------
	// Helper: find a data row by its identity (docname or name or idx)
	// ------------------------------------------------------------------
	const find_row = (ref_doc) => {
		return dialog.fields_dict.trans_items.df.data.find(
			(d) =>
				(ref_doc.docname && d.docname === ref_doc.docname) ||
				(ref_doc.name && d.name === ref_doc.name) ||
				(ref_doc.idx && d.idx === ref_doc.idx)
		);
	};

	// ------------------------------------------------------------------
	// Recalculation helpers
	// ------------------------------------------------------------------

	/** Given a changed discount %, update rate and discount_amount in the row */
	const apply_discount_pct = (row, disc_pct) => {
		const plr = flt(row.price_list_rate);
		if (!plr) return false;
		const new_rate = flt(plr * (1 - disc_pct / 100.0), get_precision("rate"));
		row.rate = new_rate < 0 ? 0 : new_rate;
		row.discount_amount = flt(plr - row.rate, get_precision("discount_amount"));
		row.discount_percentage = disc_pct < 0 ? 0 : flt(disc_pct, get_precision("discount_percentage"));
		return true;
	};

	/** Given a changed discount amount, update rate and discount_percentage in the row */
	const apply_discount_amt = (row, disc_amt) => {
		const plr = flt(row.price_list_rate);
		if (!plr) return false;
		const new_rate = flt(plr - disc_amt, get_precision("rate"));
		row.rate = new_rate < 0 ? 0 : new_rate;
		row.discount_percentage = flt(
			((plr - row.rate) / plr) * 100.0,
			get_precision("discount_percentage")
		);
		row.discount_amount = flt(disc_amt, get_precision("discount_amount"));
		return true;
	};

	/** Given a changed rate, back-calculate discount % and discount amount */
	const apply_rate = (row, rate) => {
		const plr = flt(row.price_list_rate);
		if (!plr) return false;
		const diff = plr - rate;
		// rate > price_list_rate means margin scenario — don't show negative discount
		row.discount_percentage = diff > 0 ? flt((diff / plr) * 100.0, get_precision("discount_percentage")) : 0;
		row.discount_amount = diff > 0 ? flt(diff, get_precision("discount_amount")) : 0;
		return true;
	};

	const no_plr_warning = () => {
		frappe.show_alert({
			message: __("Price List Rate is not set for this item; cannot calculate discount."),
			indicator: "orange",
		});
	};

	// ------------------------------------------------------------------
	// Build initial data rows from frm.doc.items
	// Pricing Rule values (discount_percentage, discount_amount, rate)
	// are already stored on each Sales Order Item row — just read them.
	// ------------------------------------------------------------------
	this.data = frm.doc[opts.child_docname].map((d) => {
		return {
			docname: d.name,
			name: d.name,
			item_code: d.item_code,
			delivery_date: d.delivery_date,
			schedule_date: d.schedule_date,
			conversion_factor: d.conversion_factor,
			qty: d.qty,
			price_list_rate: flt(d.price_list_rate) || 0,
			rate: flt(d.rate) || 0,
			// Pricing Rule already set these on the SO Item row:
			discount_percentage: flt(d.discount_percentage) || 0,
			discount_amount: flt(d.discount_amount) || 0,
			uom: d.uom,
			fg_item: d.fg_item,
			fg_item_qty: d.fg_item_qty,
		};
	});

	// ------------------------------------------------------------------
	// Field definitions
	// ------------------------------------------------------------------
	const fields = [
		{
			fieldtype: "Data",
			fieldname: "docname",
			read_only: 1,
			hidden: 1,
		},
		{
			fieldtype: "Link",
			fieldname: "item_code",
			options: "Item",
			in_list_view: 1,
			read_only: 0,
			disabled: 0,
			label: __("Item Code"),
			get_query: function () {
				let filters;
				if (frm.doc.doctype === "Sales Order") {
					filters = { is_sales_item: 1 };
				} else if (frm.doc.doctype === "Purchase Order") {
					if (frm.doc.is_subcontracted) {
						filters = frm.doc.is_old_subcontracting_flow
							? { is_sub_contracted_item: 1 }
							: { is_stock_item: 0 };
					} else {
						filters = { is_purchase_item: 1 };
					}
				}
				return {
					query: "erpnext.controllers.queries.item_query",
					filters: filters,
				};
			},
			change: function () {
				const me = this;

				frappe.call({
					method: "erpnext.stock.get_item_details.get_item_details",
					args: {
						doc: frm.doc,
						args: JSON.stringify({
							item_code: this.value,
							set_warehouse: frm.doc.set_warehouse,
							customer: frm.doc.customer || frm.doc.party_name,
							quotation_to: frm.doc.quotation_to,
							supplier: frm.doc.supplier,
							currency: frm.doc.currency,
							is_internal_supplier: frm.doc.is_internal_supplier,
							is_internal_customer: frm.doc.is_internal_customer,
							conversion_rate: frm.doc.conversion_rate,
							price_list: frm.doc.selling_price_list || frm.doc.buying_price_list,
							price_list_currency: frm.doc.price_list_currency,
							plc_conversion_rate: frm.doc.plc_conversion_rate,
							company: frm.doc.company,
							order_type: frm.doc.order_type,
							is_pos: cint(frm.doc.is_pos),
							is_return: cint(frm.doc.is_return),
							is_subcontracted: frm.doc.is_subcontracted,
							ignore_pricing_rule: frm.doc.ignore_pricing_rule,
							doctype: frm.doc.doctype,
							name: frm.doc.name,
							qty: me.doc.qty || 1,
							uom: me.doc.uom,
							pos_profile: cint(frm.doc.is_pos) ? frm.doc.pos_profile : "",
							tax_category: frm.doc.tax_category,
							child_doctype: frm.doc.doctype + " Item",
							is_old_subcontracting_flow: frm.doc.is_old_subcontracting_flow,
						}),
					},
					callback: function (r) {
						if (!r.message) return;

						const msg = r.message;
						// `msg.rate` is the Pricing Rule–applied rate (final rate).
						// `msg.price_list_rate` is the undiscounted list price.
						// `msg.discount_percentage` / `msg.discount_amount` are from Pricing Rule.
						const plr         = flt(msg.price_list_rate) || 0;
						const final_rate   = flt(msg.rate) || plr;
						const disc_pct     = flt(msg.discount_percentage) || 0;
						const disc_amt     = flt(msg.discount_amount) || 0;

						const row = dialog.fields_dict.trans_items.df.data.find(
							(doc) => doc.idx == me.doc.idx
						);
						if (row) {
							Object.assign(row, {
								conversion_factor: me.doc.conversion_factor || msg.conversion_factor,
								uom:               me.doc.uom || msg.uom,
								qty:               me.doc.qty || msg.qty,
								price_list_rate:   plr,
								// Use Pricing Rule rate; preserve manual edit only if already set
								rate:              me.doc.rate || final_rate,
								discount_percentage: disc_pct,
								discount_amount:     disc_amt,
								bom_no:            msg.bom_no,
							});
							dialog.fields_dict.trans_items.grid.refresh();
						}
					},
				});
			},
		},
		{
			fieldtype: "Link",
			fieldname: "uom",
			options: "UOM",
			read_only: 0,
			label: __("UOM"),
			reqd: 1,
			onchange: function () {
				frappe.call({
					method: "erpnext.stock.get_item_details.get_conversion_factor",
					args: { item_code: this.doc.item_code, uom: this.value },
					callback: (r) => {
						if (!r.exc) {
							if (this.doc.conversion_factor === r.message.conversion_factor) return;
							const docname = this.doc.docname;
							dialog.fields_dict.trans_items.df.data.some((doc) => {
								if (doc.docname === docname) {
									doc.conversion_factor = r.message.conversion_factor;
									dialog.fields_dict.trans_items.grid.refresh();
									return true;
								}
							});
						}
					},
				});
			},
		},
		{
			fieldtype: "Float",
			fieldname: "qty",
			default: 0,
			read_only: 0,
			in_list_view: 1,
			label: __("Qty"),
			precision: get_precision("qty"),
		},
		// Hidden anchor — carries price_list_rate for discount calculations
		{
			fieldtype: "Currency",
			fieldname: "price_list_rate",
			options: "currency",
			default: 0,
			read_only: 1,
			hidden: 1,
			label: __("Price List Rate"),
		},
		{
			fieldtype: "Currency",
			fieldname: "rate",
			options: "currency",
			default: 0,
			read_only: 0,
			in_list_view: 1,
			label: __("Rate"),
			precision: get_precision("rate"),
			// User edits rate → back-calculate discount fields
			onchange: function () {
				const row = this.doc;
				const target = find_row(row);
				if (!target) return;

				if (!flt(target.price_list_rate)) {
					// No price list rate — nothing to back-calculate, just clear discounts
					target.discount_percentage = 0;
					target.discount_amount = 0;
					dialog.fields_dict.trans_items.grid.refresh();
					return;
				}
				if (apply_rate(target, flt(row.rate))) {
					dialog.fields_dict.trans_items.grid.refresh();
				}
			},
		},
		// ---- NEW: Discount % ----
		{
			fieldtype: "Percent",
			fieldname: "discount_percentage",
			default: 0,
			read_only: 0,
			in_list_view: 1,
			label: __("Discount %"),
			precision: get_precision("discount_percentage"),
			// Pricing Rule discount shows here on row open; user can override it
			onchange: function () {
				const row = this.doc;
				const target = find_row(row);
				if (!target) return;

				if (!flt(target.price_list_rate)) {
					no_plr_warning();
					return;
				}
				if (apply_discount_pct(target, flt(row.discount_percentage))) {
					dialog.fields_dict.trans_items.grid.refresh();
				}
			},
		},
		// ---- NEW: Discount Amount ----
		{
			fieldtype: "Currency",
			fieldname: "discount_amount",
			options: "currency",
			default: 0,
			read_only: 0,
			in_list_view: 1,
			label: __("Disc. Amt"),
			precision: get_precision("discount_amount"),
			onchange: function () {
				const row = this.doc;
				const target = find_row(row);
				if (!target) return;

				if (!flt(target.price_list_rate)) {
					no_plr_warning();
					return;
				}
				if (apply_discount_amt(target, flt(row.discount_amount))) {
					dialog.fields_dict.trans_items.grid.refresh();
				}
			},
		},
	];

	// Splice in delivery_date / schedule_date + conversion_factor for SO / PO
	if (frm.doc.doctype === "Sales Order" || frm.doc.doctype === "Purchase Order") {
		fields.splice(2, 0, {
			fieldtype: "Date",
			fieldname: frm.doc.doctype === "Sales Order" ? "delivery_date" : "schedule_date",
			in_list_view: 1,
			label: frm.doc.doctype === "Sales Order" ? __("Delivery Date") : __("Reqd by date"),
			reqd: 1,
		});
		fields.splice(3, 0, {
			fieldtype: "Float",
			fieldname: "conversion_factor",
			label: __("Conversion Factor"),
			precision: get_precision("conversion_factor"),
		});
	}

	// Subcontracting PO: FG item fields (unchanged from core)
	if (
		frm.doc.doctype === "Purchase Order" &&
		frm.doc.is_subcontracted &&
		!frm.doc.is_old_subcontracting_flow
	) {
		fields.push(
			{
				fieldtype: "Link",
				fieldname: "fg_item",
				options: "Item",
				reqd: 1,
				in_list_view: 0,
				read_only: 0,
				disabled: 0,
				label: __("Finished Good Item"),
				get_query: () => ({
					filters: {
						is_stock_item: 1,
						is_sub_contracted_item: 1,
						default_bom: ["!=", ""],
					},
				}),
			},
			{
				fieldtype: "Float",
				fieldname: "fg_item_qty",
				reqd: 1,
				default: 0,
				read_only: 0,
				in_list_view: 0,
				label: __("Finished Good Item Qty"),
				precision: get_precision("fg_item_qty"),
			}
		);
	}

	// ------------------------------------------------------------------
	// Build and show the dialog
	// ------------------------------------------------------------------
	let dialog = new frappe.ui.Dialog({
		title: __("Update Items"),
		size: "extra-large",
		fields: [
			{
				fieldname: "trans_items",
				fieldtype: "Table",
				label: "Items",
				cannot_add_rows: cannot_add_row,
				in_place_edit: false,
				reqd: 1,
				data: this.data,
				get_data: () => this.data,
				fields: fields,
			},
		],
		primary_action: function () {
			if (frm.doctype === "Sales Order" && has_reserved_stock) {
				this.hide();
				frappe.confirm(
					__("The reserved stock will be released when you update items. Are you certain you wish to proceed?"),
					() => this.update_items()
				);
			} else {
				this.update_items();
			}
		},
		update_items: function () {
			// Send adjusted `rate` in the payload.
			// Server derives discount_percentage / discount_amount from
			// price_list_rate vs rate — no extra fields needed.
			const trans_items = this.get_values()["trans_items"].filter(
				(item) => !!item.item_code
			);

			frappe.call({
				method: "erpnext.controllers.accounts_controller.update_child_qty_rate",
				freeze: true,
				args: {
					parent_doctype: frm.doc.doctype,
					trans_items: trans_items,
					parent_doctype_name: frm.doc.name,
					child_docname: child_docname,
				},
				callback: function () {
					frm.reload_doc();
				},
			});
			this.hide();
			refresh_field("items");
		},
		primary_action_label: __("Update"),
	});

	dialog.show();
};
