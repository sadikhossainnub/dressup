// Copyright (c) 2026, Prime Technology of Bangladesh and contributors
// For license information, please see license.txt

frappe.ui.form.on("Asset Maintenance Log", {
    refresh(frm) {
        // Set query filters for accounts
        frm.set_query("expense_account", function () {
            return {
                filters: {
                    company: frm.doc.company,
                    root_type: "Expense",
                    is_group: 0,
                },
            };
        });

        frm.set_query("paid_from_account", function () {
            return {
                filters: {
                    company: frm.doc.company,
                    account_type: ["in", ["Cash", "Bank"]],
                    is_group: 0,
                },
            };
        });
    },

    paid_by(frm) {
        // Toggle accounting section visibility
        frm.toggle_display(
            "accounting_details_section",
            frm.doc.paid_by === "Company"
        );
    },
});
