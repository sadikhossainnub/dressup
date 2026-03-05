// Copyright (c) 2026, Prime Technology of Bangladesh and contributors
// For license information, please see license.txt

frappe.ui.form.on("Rented Asset", {
    refresh(frm) {
        // Make Rent Payment button
        if (frm.doc.status === "Active" && frm.doc.supplier && !frm.is_new()) {
            frm.add_custom_button(__("Make Rent Payment"), function () {
                frm.call({
                    method: "make_rent_payment",
                    doc: frm.doc,
                    callback: function (r) {
                        if (r.message) {
                            var doc = frappe.model.sync(r.message);
                            frappe.set_route("Form", "Payment Entry", doc[0].name);
                        }
                    },
                });
            }, __("Actions"));
        }

        // Pay Deposit button
        if (!frm.doc.deposit_paid && frm.doc.security_deposit > 0 && !frm.is_new()) {
            frm.add_custom_button(__("Pay Deposit"), function () {
                frappe.confirm(
                    __("Create Journal Entry for Security Deposit of {0}?", [
                        format_currency(frm.doc.security_deposit),
                    ]),
                    function () {
                        frm.call({
                            method: "pay_deposit",
                            doc: frm.doc,
                            callback: function () {
                                frm.reload_doc();
                            },
                        });
                    }
                );
            }, __("Actions"));
        }

        // Refund Deposit button
        if (frm.doc.deposit_paid && !frm.doc.deposit_refunded && !frm.is_new()) {
            frm.add_custom_button(__("Refund Deposit"), function () {
                frappe.confirm(
                    __("Create Journal Entry for Deposit Refund of {0}?", [
                        format_currency(frm.doc.security_deposit),
                    ]),
                    function () {
                        frm.call({
                            method: "refund_deposit",
                            doc: frm.doc,
                            callback: function () {
                                frm.reload_doc();
                            },
                        });
                    }
                );
            }, __("Actions"));
        }

        // Renew Agreement button
        if (!frm.is_new()) {
            frm.add_custom_button(__("Renew Agreement"), function () {
                frappe.new_doc("Rent Agreement Renewal", {
                    rented_asset: frm.doc.name,
                });
            }, __("Actions"));
        }

        // Set account query filters
        frm.set_query("rent_expense_account", function () {
            return {
                filters: {
                    company: frm.doc.company,
                    root_type: "Expense",
                    is_group: 0,
                },
            };
        });

        frm.set_query("security_deposit_account", function () {
            return {
                filters: {
                    company: frm.doc.company,
                    root_type: "Asset",
                    is_group: 0,
                },
            };
        });

        frm.set_query("maintenance_expense_account", function () {
            return {
                filters: {
                    company: frm.doc.company,
                    root_type: "Expense",
                    is_group: 0,
                },
            };
        });

        frm.set_query("default_cost_center", function () {
            return {
                filters: {
                    company: frm.doc.company,
                    is_group: 0,
                },
            };
        });
    },

    asset_type(frm) {
        // Show/hide machinery section based on asset_type
        frm.toggle_display(
            "machinery_details_section",
            frm.doc.asset_type === "Machinery"
        );
    },
});
