frappe.ui.form.on('Quality Inspection', {
    onload: function (frm) {
        // Add "Pre Production Sample" to Reference Type options
        let reference_type_field = frm.fields_dict.reference_type;
        if (reference_type_field) {
            let current_options = reference_type_field.df.options;
            if (!current_options.includes('Pre Production Sample')) {
                reference_type_field.df.options = current_options + '\nPre Production Sample';
                frm.refresh_field('reference_type');
            }
        }
    },

    refresh: function (frm) {
        // Set query for reference_name when reference_type is Pre Production Sample
        if (frm.doc.reference_type === 'Pre Production Sample') {
            frm.set_query('reference_name', function () {
                return {
                    filters: {
                        docstatus: 0  // Only draft PPS documents
                    }
                };
            });
        }
    },

    reference_type: function (frm) {
        // Clear reference_name when reference_type changes
        if (frm.doc.reference_type === 'Pre Production Sample') {
            frm.set_query('reference_name', function () {
                return {
                    filters: {
                        docstatus: 0  // Only draft PPS documents
                    }
                };
            });
        }
    },

    reference_name: function (frm) {
        // Auto-fetch item_code from PPS when reference_name is selected
        if (frm.doc.reference_type === 'Pre Production Sample' && frm.doc.reference_name) {
            frappe.db.get_value('Pre Production Sample', frm.doc.reference_name, ['item_code', 'link_nsnp'], function (r) {
                if (r) {
                    if (r.item_code) {
                        frm.set_value('item_code', r.item_code);
                    }
                    if (r.link_nsnp && !frm.doc.quality_inspection_template) {
                        frm.set_value('quality_inspection_template', r.link_nsnp);
                    }
                }
            });
        }
    }
});
