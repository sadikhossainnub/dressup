// Copyright (c) 2026, Prime Technology of Bangladesh and contributors
// For license information, please see license.txt

frappe.ui.form.on("Loyalty Tier Upgrade Settings", {
	refresh(frm) {
		frm.set_intro(
			__(
				"Configure SMS/Email notification channels for loyalty tier upgrades, downgrades, and point expiry warnings. " +
				"SMS requires Frappe <b>SMS Settings</b> to be configured with a gateway."
			),
			"blue"
		);
	},
});

