frappe.ui.form.on("Appointment Letter", {
	onload(frm) {
		// Set read-only fields inside child table to make sure users can't edit
		frm.set_df_property("custom_salary_components", "read_only", 1);
	},
	custom_basic_amount(frm) {
		calculate_salary(frm);
	},
	custom_salary_structure(frm) {
		calculate_salary(frm);
	}
});

function calculate_salary(frm) {
	if (!frm.doc.custom_basic_amount || !frm.doc.custom_salary_structure) {
		// If either is empty, we clear the table and reset gross
		frm.clear_table("custom_salary_components");
		frm.refresh_field("custom_salary_components");
		frm.set_value("custom_gross_salary", 0.0);
		return;
	}

	frappe.call({
		method: "dressup.dressup.api.appointment_letter.get_calculated_salary_components",
		args: {
			salary_structure: frm.doc.custom_salary_structure,
			basic_amount: frm.doc.custom_basic_amount
		},
		freeze: true,
		freeze_message: __("Calculating salary components..."),
		callback(r) {
			if (r.message) {
				frm.clear_table("custom_salary_components");
				if (r.message.components) {
					r.message.components.forEach(c => {
						let row = frm.add_child("custom_salary_components");
						row.salary_component = c.salary_component;
						row.abbr = c.abbr;
						row.component_type = c.component_type;
						row.formula = c.formula;
						row.condition = c.condition;
						row.amount = c.amount;
					});
				}
				frm.refresh_field("custom_salary_components");
				frm.set_value("custom_gross_salary", r.message.gross_salary);
			}
		}
	});
}
