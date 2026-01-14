frappe.ui.form.on('Barcode Label Template', {
    refresh: function (frm) {
        if (!frm.doc.__islocal) {
            frm.add_custom_button('Design Label', () => {
                frm.trigger('render_designer');
            });
            // Auto-render if section is visible (simplistic approach)
            frm.trigger('render_designer');
        }
    },

    render_designer: function (frm) {
        const wrapper = frm.get_field('section_break_design').wrapper;
        if (!wrapper) return;

        wrapper.innerHTML = ''; // Clear previous

        // Ensure LabelDesigner class is loaded
        if (typeof LabelDesigner === 'undefined') {
            frappe.require('/assets/dressup/js/label_designer.js', () => {
                new LabelDesigner(wrapper, {
                    width: frm.doc.label_width,
                    height: frm.doc.label_height,
                    data: JSON.parse(frm.doc.design_data || '[]'),
                    on_save: (data) => {
                        frm.set_value('design_data', JSON.stringify(data));
                        frm.dirty();
                    }
                });
            });
        } else {
            new LabelDesigner(wrapper, {
                width: frm.doc.label_width,
                height: frm.doc.label_height,
                data: JSON.parse(frm.doc.design_data || '[]'),
                on_save: (data) => {
                    frm.set_value('design_data', JSON.stringify(data));
                    frm.dirty();
                }
            });
        }
    },

    label_width: function (frm) {
        if (window.cur_designer) {
            window.cur_designer.update_canvas_size(frm.doc.label_width, frm.doc.label_height);
        }
    },

    label_height: function (frm) {
        if (window.cur_designer) {
            window.cur_designer.update_canvas_size(frm.doc.label_width, frm.doc.label_height);
        }
    }
});
