// Copyright (c) 2026, Prime Technology of Bangladesh and contributors
// For license information, please see license.txt
//
// Adds a "Create Customer" button (or a "View Customer" button when already
// linked) to the Employee form.

frappe.ui.form.on("Employee", {
	refresh(frm) {
		// Don't show anything on new unsaved records
		if (frm.is_new()) return;

		if (!frm.doc.custom_linked_customer) {
			// ── No customer linked yet → show "Create Customer" ──────────────
			frm.add_custom_button(__("Create Customer"), function () {
				frappe.confirm(
					__("Create a Customer record for this employee?"),
					function () {
						// Confirmed — call the server method
						frappe.call({
							method: "dressup.dressup.custom_scripts.employee.create_customer_from_employee",
							args: { employee_name: frm.doc.name },
							freeze: true,
							freeze_message: __("Creating Customer…"),
							callback(r) {
								if (r.exc) {
									// Server threw an exception — r.exc contains the
									// traceback; r._server_messages has the user-visible
									// message. frappe.call already shows it, but we add
									// an explicit alert so it is not silently swallowed.
									frappe.msgprint({
										title: __("Customer Creation Failed"),
										indicator: "red",
										message: r._server_messages
											? JSON.parse(r._server_messages).join("<br>")
											: __("An unexpected error occurred. Please check the Error Log."),
									});
									return;
								}
								if (r.message) {
									frappe.show_alert({
										message: r.message.message,
										indicator: r.message.created ? "green" : "blue",
									}, 6);
									// Reload so the linked customer field renders
									// and the button switches to "View Customer"
									frm.reload_doc();
								}
							},
						});
					}
					// No-op on cancel — dialog simply closes
				);
			}, __("Actions"));

		} else {
			// ── Customer already linked → show "View Customer" ───────────────
			frm.add_custom_button(__("View Customer"), function () {
				frappe.set_route("Form", "Customer", frm.doc.custom_linked_customer);
			}, __("Actions"));

			// Add a small dashboard indicator for quick visual confirmation
			frm.dashboard.add_indicator(
				__("Customer: {0}", [frm.doc.custom_linked_customer]),
				"blue"
			);
		}
	},
});
