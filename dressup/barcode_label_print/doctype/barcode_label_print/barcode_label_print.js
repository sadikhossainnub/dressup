frappe.ui.form.on('Barcode Label Print', {
    setup: function (frm) {
        frm.set_query('batch_no', function () {
            return {
                filters: {
                    item: frm.doc.item_code
                }
            };
        });
        frm.set_query('serial_no', function () {
            return {
                filters: {
                    item_code: frm.doc.item_code
                }
            };
        });
    },
    item_code: function (frm) {
        if (frm.doc.item_code) {
            frappe.db.get_value('Item', frm.doc.item_code, ['item_name'], function (r) {
                if (r) {
                    frm.set_value('item_name', r.item_name);
                }
            });
        }
    },
    batch_no: function (frm) {
        if (frm.doc.batch_no) {
            frappe.db.get_value('Batch', frm.doc.batch_no, 'expiry_date', function (r) {
                if (r) {
                    frm.set_value('expiry_date', r.expiry_date);
                }
            });
        }
    }
});
