// Copyright (c) 2026, Prime Technology of Bangladesh and contributors
// For license information, please see license.txt

frappe.ui.form.on("Rent Agreement Renewal", {
    refresh(frm) {
        // Nothing extra needed — fetch_from handles auto-fill
    },

    new_monthly_rent(frm) {
        calculate_rent_change(frm);
    },

    previous_rent(frm) {
        calculate_rent_change(frm);
    },
});

function calculate_rent_change(frm) {
    if (frm.doc.previous_rent && frm.doc.previous_rent > 0 && frm.doc.new_monthly_rent) {
        var change =
            ((frm.doc.new_monthly_rent - frm.doc.previous_rent) / frm.doc.previous_rent) * 100;
        frm.set_value("rent_change_percentage", flt(change, 2));
    } else {
        frm.set_value("rent_change_percentage", 0);
    }
}
