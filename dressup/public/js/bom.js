frappe.ui.form.on("BOM", {
	refresh(frm) {
		frm.trigger("setup_pps_mapping");
	},

	setup_pps_mapping(frm) {
		// When a PPS is selected on BOM, auto-set Tech Pack No from PPS.tech_pack_no.
		// Supports both legacy and custom fieldnames across different databases.
		const pps_field = frm.doc.hasOwnProperty("pre_production_sample")
			? "pre_production_sample"
			: (frm.doc.hasOwnProperty("custom_pre_production_sample") ? "custom_pre_production_sample" : null);

		if (!pps_field) return;

		frm.set_query(pps_field, () => ({
			filters: {
				docstatus: 1,
			},
		}));
	},

	pre_production_sample(frm) {
		set_tech_pack_from_pps(frm, frm.doc.pre_production_sample);
	},

	custom_pre_production_sample(frm) {
		set_tech_pack_from_pps(frm, frm.doc.custom_pre_production_sample);
	},
});

function set_tech_pack_from_pps(frm, pps_name) {
	if (!pps_name) return;

	frappe.db.get_value("Pre Production Sample", pps_name, ["tech_pack_no"], (r) => {
		const tech_pack_no = r && r.tech_pack_no ? r.tech_pack_no : null;
		if (!tech_pack_no) return;

		if (frm.doc.hasOwnProperty("custom_tech_pack_no")) {
			frm.set_value("custom_tech_pack_no", tech_pack_no);
		}
		if (frm.doc.hasOwnProperty("tech_pack_no")) {
			frm.set_value("tech_pack_no", tech_pack_no);
		}
	});
}

