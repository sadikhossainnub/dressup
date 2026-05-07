frappe.ui.form.on("Work Order", {
	onload(frm) {
		frm.trigger("setup_bom_mapping");
		if (frm.doc.bom_no) {
			frm.trigger("sync_from_bom");
		}
	},

	refresh(frm) {
		frm.trigger("setup_bom_mapping");
		if (frm.doc.bom_no) {
			frm.trigger("sync_from_bom");
		}
	},

	setup_bom_mapping(frm) {
		// When BOM is selected, auto-set Tech Pack No + PPS link from BOM.
		frm.set_query("bom_no", () => ({
			filters: {
				docstatus: 1,
				is_active: 1,
			},
		}));
	},

	bom_no(frm) {
		frm.trigger("sync_from_bom");
	},

	sync_from_bom(frm) {
		if (!frm.doc.bom_no) {
			if (frm.doc.hasOwnProperty("tech_pack_no")) frm.set_value("tech_pack_no", "");
			if (frm.doc.hasOwnProperty("pre_production_sample")) frm.set_value("pre_production_sample", "");
			return;
		}

		frappe.db.get_value(
			"BOM",
			frm.doc.bom_no,
			["tech_pack_no", "pre_production_sample"],
			(r) => {
				if (!r) return;

				// Tech Pack No
				const tech_pack_no = r.tech_pack_no;
				if (tech_pack_no) {
					if (frm.doc.hasOwnProperty("tech_pack_no")) frm.set_value("tech_pack_no", tech_pack_no);
				}

				// Pre Production Sample
				const pps = r.pre_production_sample;
				if (pps) {
					if (frm.doc.hasOwnProperty("pre_production_sample")) frm.set_value("pre_production_sample", pps);
				}
			}
		);
	},
});

