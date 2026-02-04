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
        let field = frm.get_field('designer_html');
        if (!field || !field.wrapper) {
            console.log("Designer wrapper not ready yet...");
            return;
        }

        const wrapper = field.wrapper;
        wrapper.innerHTML = '<div class="text-muted p-3">Loading Designer...</div>';

        const init_designer = () => {
            try {
                if (typeof LabelDesigner === 'undefined') {
                    frappe.msgprint(__('LabelDesigner class not found. Please ensure label_designer.js is loaded.'));
                    return;
                }

                new LabelDesigner(wrapper, {
                    width: frm.doc.label_width || 50,
                    height: frm.doc.label_height || 25,
                    data: JSON.parse(frm.doc.design_data || '[]'),
                    on_save: (data) => {
                        frm.set_value('design_data', JSON.stringify(data));
                    }
                });
            } catch (e) {
                console.error("Designer Init Error:", e);
                wrapper.innerHTML = `<div class="alert alert-danger">Error loading designer: ${e.message}</div>`;
            }
        };

        if (typeof LabelDesigner === 'undefined') {
            frappe.require('/assets/dressup/js/label_designer.js', init_designer);
        } else {
            init_designer();
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
