// Copyright (c) 2026, Prime Technology of Bangladesh and contributors
// For license information, please see license.txt

frappe.ui.form.on("Loyalty Downgrade Settings", {
	refresh(frm) {
		// Add a visual indicator when downgrade is active
		if (frm.doc.enabled) {
			frm.set_intro(
				__("Loyalty Downgrade is <b>ENABLED</b>. The scheduler will automatically check and downgrade customers based on the configured rules."),
				"green"
			);
		} else {
			frm.set_intro(
				__("Loyalty Downgrade is currently <b>DISABLED</b>. Enable it and configure rules to start automatic tier downgrade."),
				"yellow"
			);
		}

		// Add a button to manually trigger the downgrade check
		if (frm.doc.enabled) {
			frm.add_custom_button(__("Run Downgrade Check Now"), function () {
				frappe.call({
					method: "dressup.dressup.loyalty_downgrade.check_loyalty_tier_downgrade",
					freeze: true,
					freeze_message: __("Checking loyalty tier downgrade for all customers..."),
					callback: function (r) {
						if (!r.exc) {
							frappe.msgprint({
								title: __("Downgrade Check Complete"),
								message: r.message || __("Downgrade check completed successfully."),
								indicator: "green",
							});
						}
					},
				});
			}, __("Actions"));
		}
	},
});
