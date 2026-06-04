// Copyright (c) 2026, Prime Technology of Bangladesh and contributors
// For license information, please see license.txt

frappe.ui.form.on("Job Applicant Invitation", {
	refresh: function(frm) {
		if (frm.doc.docstatus === 0) {
			// Draft Actions
			if (!frm.is_new()) {
				frm.add_custom_button(__("Send Email Invitation"), function() {
					frm.events.send_email(frm);
				}, __("Actions"));
			}
		}

		if (frm.doc.docstatus === 1) {
			// Submitted Actions
			if (frm.doc.rsvp_status === "Pending") {
				frm.add_custom_button(__("Confirm RSVP"), function() {
					frm.events.update_rsvp_status(frm, "Confirmed");
				}, __("RSVP"));

				frm.add_custom_button(__("Decline RSVP"), function() {
					frm.events.update_rsvp_status(frm, "Declined");
				}, __("RSVP"));
			}

			if (frm.doc.rsvp_status === "Confirmed" && !frm.doc.interview) {
				frm.add_custom_button(__("Create HRMS Interview"), function() {
					frm.events.create_interview(frm);
				}, __("Actions"));
			}
		}

		// Customize Indicator colors
		if (frm.doc.status === "Draft") {
			frm.set_intro(__("This invitation is in Draft. Fill in the details and send the email invitation to the candidate."));
		} else if (frm.doc.status === "Sent") {
			frm.set_intro(__("Invitation has been sent. Awaiting candidate RSVP response."));
		} else if (frm.doc.status === "Confirmed") {
			frm.set_intro(__("Candidate has confirmed attendance. An HRMS Interview has been scheduled."));
		} else if (frm.doc.status === "Declined") {
			frm.set_intro(__("Candidate has declined the invitation."), "red");
		}
	},

	send_email: function(frm) {
		frappe.confirm(
			__("Are you sure you want to send the formal email invitation to {0}?", [frm.doc.applicant_name]),
			function() {
				frappe.dom.freeze(__("Sending Invitation Email..."));
				frm.call({
					doc: frm.doc,
					method: "send_invitation_email",
					callback: function(r) {
						frappe.dom.unfreeze();
						frm.reload_doc();
					}
				});
			}
		);
	},

	update_rsvp_status: function(frm, status) {
		frappe.confirm(
			__("Are you sure you want to mark RSVP status as {0}?", [status]),
			function() {
				frappe.dom.freeze(__("Updating RSVP..."));
				frm.call({
					doc: frm.doc,
					method: "update_rsvp",
					args: {
						rsvp_status: status
					},
					callback: function(r) {
						frappe.dom.unfreeze();
						frm.reload_doc();
					}
				});
			}
		);
	},

	create_interview: function(frm) {
		frappe.dom.freeze(__("Creating HRMS Interview..."));
		frm.call({
			doc: frm.doc,
			method: "create_hrms_interview",
			callback: function(r) {
				frappe.dom.unfreeze();
				frm.reload_doc();
			}
		});
	}
});
