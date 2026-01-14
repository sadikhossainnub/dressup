frappe.ui.form.on('Barcode Label Print', {
    refresh: function(frm) {
        frm.trigger('render_preview');
    },

    label_template: function(frm) {
        frm.trigger('render_preview');
    },

    render_preview: function(frm) {
        if (frm.doc.items && frm.doc.items.length > 0 && frm.doc.label_template) {
            frm.save_or_update();
        }
    }
});

frappe.ui.form.on('Barcode Label Item', {
    item_code: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.item_code) {
            frappe.db.get_value('Item', row.item_code, ['item_name', 'standard_rate'], function(r) {
                if (r) {
                    frappe.model.set_value(cdt, cdn, 'item_name', r.item_name);
                    frappe.model.set_value(cdt, cdn, 'price', r.standard_rate);
                }
            });
        }
    },

    batch_no: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.batch_no) {
            frappe.db.get_value('Batch', row.batch_no, 'expiry_date', function(r) {
                if (r) {
                    frappe.model.set_value(cdt, cdn, 'expiry_date', r.expiry_date);
                }
            });
        }
    }
});
