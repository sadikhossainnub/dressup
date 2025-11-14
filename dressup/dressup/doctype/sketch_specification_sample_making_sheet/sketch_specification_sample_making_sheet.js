// Copyright (c) 2024, DressUp and contributors
// For license information, please see license.txt

frappe.ui.form.on('Sketch Specification Sample Making Sheet', {
	refresh(frm) {
		if (frm.is_new() && !frm.doc.designer) {
			frappe.db.get_value('Employee', {'user_id': frappe.session.user}, 'name')
				.then(r => {
					if (r.message?.name) {
						frm.set_value('designer', r.message.name);
					}
				})
				.catch(err => {
					console.warn('Could not fetch employee data:', err);
				});
		}
	}
});