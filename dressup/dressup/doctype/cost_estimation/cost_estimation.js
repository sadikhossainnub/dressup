// Copyright (c) 2025, Prime Technology of Bangladesh and contributors
// For license information, please see license.txt

frappe.ui.form.on("Cost Estimation", {
	refresh(frm) {
		frm.trigger('calculate_totals');
	},
	
	calculate_totals(frm) {
		const tables = [
			{name: 'materials', qty_field: 'qty', rate_field: 'rate'},
			{name: 'accessories', qty_field: 'qty', rate_field: 'unit_price'},
			{name: 'cutting', qty_field: 'quantity', rate_field: 'rate'},
			{name: 'sewing', qty_field: 'quantity', rate_field: 'rate'},
			{name: 'hand_work_estimation', qty_field: 'quantity', rate_field: 'rate'}
		];
		
		tables.forEach(table => {
			if (frm.doc[table.name]) {
				frm.doc[table.name].forEach(row => {
					if (row[table.qty_field] && row[table.rate_field]) {
						row.amount = row[table.qty_field] * row[table.rate_field];
					}
				});
			}
		});
		
		frm.refresh_fields();
	}
});

// Material calculations
frappe.ui.form.on("Cost Estimation Material", {
	qty(frm, cdt, cdn) {
		calculate_material_amount(frm, cdt, cdn);
	},
	
	rate(frm, cdt, cdn) {
		calculate_material_amount(frm, cdt, cdn);
	}
});

// Accessory calculations
frappe.ui.form.on("Cost Estimation Accessory", {
	qty(frm, cdt, cdn) {
		calculate_accessory_amount(frm, cdt, cdn);
	},
	
	unit_price(frm, cdt, cdn) {
		calculate_accessory_amount(frm, cdt, cdn);
	}
});

// Cutting Estimation calculations
frappe.ui.form.on("Cutting Estimation", {
	quantity(frm, cdt, cdn) {
		calculate_cutting_amount(frm, cdt, cdn);
	},
	
	rate(frm, cdt, cdn) {
		calculate_cutting_amount(frm, cdt, cdn);
	}
});

// Sewing Estimation calculations
frappe.ui.form.on("Sewing Estimation", {
	quantity(frm, cdt, cdn) {
		calculate_sewing_amount(frm, cdt, cdn);
	},
	
	rate(frm, cdt, cdn) {
		calculate_sewing_amount(frm, cdt, cdn);
	}
});

// Hand Work Estimation calculations
frappe.ui.form.on("Hand Work Estimation", {
	quantity(frm, cdt, cdn) {
		calculate_hand_work_amount(frm, cdt, cdn);
	},
	
	rate(frm, cdt, cdn) {
		calculate_hand_work_amount(frm, cdt, cdn);
	}
});

const calculation_configs = {
	materials: {qty_field: 'qty', rate_field: 'rate'},
	accessories: {qty_field: 'qty', rate_field: 'unit_price'},
	cutting: {qty_field: 'quantity', rate_field: 'rate'},
	sewing: {qty_field: 'quantity', rate_field: 'rate'},
	hand_work_estimation: {qty_field: 'quantity', rate_field: 'rate'}
};

function calculate_amount(frm, cdt, cdn, table_name) {
	const row = locals[cdt][cdn];
	const config = calculation_configs[table_name];
	if (row[config.qty_field] && row[config.rate_field]) {
		row.amount = row[config.qty_field] * row[config.rate_field];
		frm.refresh_field(table_name);
	}
}

const calculate_material_amount = (frm, cdt, cdn) => calculate_amount(frm, cdt, cdn, 'materials');
const calculate_accessory_amount = (frm, cdt, cdn) => calculate_amount(frm, cdt, cdn, 'accessories');
const calculate_cutting_amount = (frm, cdt, cdn) => calculate_amount(frm, cdt, cdn, 'cutting');
const calculate_sewing_amount = (frm, cdt, cdn) => calculate_amount(frm, cdt, cdn, 'sewing');
const calculate_hand_work_amount = (frm, cdt, cdn) => calculate_amount(frm, cdt, cdn, 'hand_work_estimation');
