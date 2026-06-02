// Copyright (c) 2026, Prime Technology of Bangladesh and contributors
// For license information, please see license.txt

frappe.ui.form.on("Job Applicant", {
	refresh(frm) {
		if (!frm.is_new()) {
			frm.add_custom_button(__("Create Invitation"), function() {
				frappe.model.with_doctype("Job Applicant Invitation", function() {
					const invitation = frappe.model.get_new_doc("Job Applicant Invitation");
					invitation.job_applicant = frm.doc.name;
					frappe.set_route("Form", "Job Applicant Invitation", invitation.name);
				});
			}, __("Actions"));

			// Let's also list invitations in the dashboard or as a link
			frm.events.show_invitation_link(frm);
		}
	},

	show_invitation_link(frm) {
		frappe.db.get_list("Job Applicant Invitation", {
			filters: { job_applicant: frm.doc.name },
			fields: ["name", "status", "rsvp_status"]
		}).then(invitations => {
			if (invitations && invitations.length > 0) {
				const invitation = invitations[0];
				let indicator = "orange";
				if (invitation.status === "Confirmed") indicator = "green";
				if (invitation.status === "Declined") indicator = "red";
				if (invitation.status === "Sent") indicator = "blue";

				frm.dashboard.clear_headline();
				frm.dashboard.add_headline(
					__("Active Invitation: {0} ({1}) RSVP: {2}", [
						`<a href="/app/job-applicant-invitation/${invitation.name}"><strong>${invitation.name}</strong></a>`,
						`<span class="indicator ${indicator}">${invitation.status}</span>`,
						`<strong>${invitation.rsvp_status}</strong>`
					])
				);
			}
		});
	}
});
