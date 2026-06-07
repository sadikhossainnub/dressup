frappe.ui.form.on('Stock Entry', {
	refresh: function(frm) {
		// Override savecancel to show a custom confirmation dialog
		frm.savecancel = function(btn, callback, on_error) {
			const me = this;
			me.validate_form_action("Cancel");
			me.ignore_doctypes_on_cancel_all = me.ignore_doctypes_on_cancel_all || [];

			frappe.call({
				method: "frappe.desk.form.linked_with.get_submitted_linked_docs",
				args: {
					doctype: me.doc.doctype,
					name: me.doc.name,
					ignore_doctypes_on_cancel_all: me.ignore_doctypes_on_cancel_all,
				},
				freeze: true,
			}).then((r) => {
				if (!r.exc) {
					let links = r.message.docs || [];
					let doctypes_to_cancel = links.map((value) => value.doctype);

					if (doctypes_to_cancel.length) {
						// Show custom option dialog
						let links_text = "";
						const doctypes = Array.from(new Set(links.map((link) => link.doctype)));

						for (let doctype of doctypes) {
							let docnames = links
								.filter((link) => link.doctype == doctype)
								.map((link) => frappe.utils.get_form_link(link.doctype, link.name, true))
								.join(", ");
							links_text += `<li><strong>${__(doctype)}</strong>: ${docnames}</li>`;
						}
						links_text = `<ul>${links_text}</ul>`;

						let confirm_message = __("{0} {1} is linked with the following submitted documents: {2}<br>Do you want to cancel all linked documents, or only cancel this Stock Entry?", [
							__(me.doc.doctype).bold(),
							me.doc.name,
							links_text,
						]);

						let d = new frappe.ui.Dialog({
							title: __("Cancel Stock Entry Options"),
							fields: [
								{
									fieldtype: "HTML",
									options: `<p class="frappe-confirm-message">${confirm_message}</p>`,
								},
							],
							primary_action_label: __("Cancel Only Stock Entry"),
							primary_action: function() {
								d.hide();
								me._cancel(btn, callback, on_error, true);
							}
						});

						let can_cancel = links.every((link) => frappe.model.can_cancel(link.doctype));
						if (can_cancel) {
							d.add_custom_button(__("Cancel All"), function() {
								d.hide();
								frappe.call({
									method: "frappe.desk.form.linked_with.cancel_all_linked_docs",
									args: {
										docs: links,
										ignore_doctypes_on_cancel_all: me.ignore_doctypes_on_cancel_all || [],
									},
									freeze: true,
									callback: (resp) => {
										if (!resp.exc) {
											me.reload_doc();
											me._cancel(btn, callback, on_error, true);
										}
									},
								});
							});
						}

						// Customize Close/Cancel callback behavior
						d.on_cancel = function() {
							me.handle_save_fail(btn, on_error);
						};

						d.show();
						return;
					}
				}
				return me._cancel(btn, callback, on_error, false);
			});
		};
	}
});
