frappe.ui.form.on("BOM", {
	refresh(frm) {
		frm.trigger("setup_pps_mapping");
		frm.trigger("set_bom_creator");
	},

	set_bom_creator(frm) {
		// Auto-fill BOM Creator with the current user's full name on new documents
		if (frm.is_new() && !frm.doc.custom_bom_creator) {
			frm.set_value("custom_bom_creator", frappe.session.user_fullname);
		}
	},

	setup_pps_mapping(frm) {
		// When a PPS is selected on BOM, auto-set Tech Pack No from PPS.tech_pack_no.
		// Uses only legacy fieldnames.
		if (!frm.doc.hasOwnProperty("pre_production_sample")) return;

		frm.set_query("pre_production_sample", () => ({
			filters: {
				docstatus: 1,
			},
		}));
	},

	pre_production_sample(frm) {
		set_tech_pack_from_pps(frm, frm.doc.pre_production_sample);
	},

	// Only legacy fieldnames are supported
});

function set_tech_pack_from_pps(frm, pps_name) {
	if (!pps_name) return;

	frappe.db.get_value("Pre Production Sample", pps_name, ["tech_pack_no"], (r) => {
		const tech_pack_no = r && r.tech_pack_no ? r.tech_pack_no : null;
		if (!tech_pack_no) return;

		if (frm.doc.hasOwnProperty("tech_pack_no")) frm.set_value("tech_pack_no", tech_pack_no);
	});
}

