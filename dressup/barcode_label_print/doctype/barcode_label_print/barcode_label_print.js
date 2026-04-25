frappe.ui.form.on('Barcode Label Print', {
    refresh: function(frm) {
        frm.trigger('render_preview');
        frm.trigger('add_bulk_buttons');
    },

    label_template: function(frm) {
        frm.trigger('render_preview');
    },

    render_preview: function(frm) {
        if (frm.doc.items && frm.doc.items.length > 0 && frm.doc.label_template) {
            frm.save_or_update();
        }
    },

    add_bulk_buttons: function(frm) {
        // Bulk Add Items button
        frm.add_custom_button(__('Bulk Add Items'), function() {
            frm.trigger('show_bulk_add_dialog');
        }, __('Add Items'));

        // Add from Item Group button
        frm.add_custom_button(__('From Item Group'), function() {
            frm.trigger('show_item_group_dialog');
        }, __('Add Items'));

        // Clear All Items button
        if (frm.doc.items && frm.doc.items.length > 0) {
            frm.add_custom_button(__('Clear All Items'), function() {
                frappe.confirm(
                    __('Are you sure you want to remove all items?'),
                    function() {
                        frm.doc.items = [];
                        frm.refresh_field('items');
                        frm.dirty();
                        frappe.show_alert({
                            message: __('All items cleared'),
                            indicator: 'orange'
                        });
                    }
                );
            }, __('Add Items'));
        }

        // Add from Serial Nos button
        frm.add_custom_button(__('From Serial Nos'), function() {
            frm.trigger('show_serial_no_dialog');
        }, __('Add Items'));
    },

    show_bulk_add_dialog: function(frm) {
        let d = new frappe.ui.Dialog({
            title: __('Bulk Add Items'),
            size: 'extra-large',
            fields: [
                {
                    fieldname: 'search_section',
                    fieldtype: 'Section Break',
                    label: __('Search & Filter')
                },
                {
                    fieldname: 'item_group',
                    fieldtype: 'Link',
                    label: __('Item Group'),
                    options: 'Item Group',
                    change: function() {
                        d.fields_dict.search_items.$input.trigger('input');
                    }
                },
                {
                    fieldname: 'col1',
                    fieldtype: 'Column Break'
                },
                {
                    fieldname: 'search_items',
                    fieldtype: 'Data',
                    label: __('Search Items'),
                    description: __('Type to search by item code or item name'),
                },
                {
                    fieldname: 'col2',
                    fieldtype: 'Column Break'
                },
                {
                    fieldname: 'default_qty',
                    fieldtype: 'Int',
                    label: __('Default Print Qty'),
                    default: 1,
                    description: __('Default quantity for newly added items')
                },
                {
                    fieldname: 'results_section',
                    fieldtype: 'Section Break',
                    label: __('Search Results')
                },
                {
                    fieldname: 'results_html',
                    fieldtype: 'HTML',
                    options: '<div class="text-muted text-center" style="padding: 40px;">Type to search for items...</div>'
                },
                {
                    fieldname: 'selected_section',
                    fieldtype: 'Section Break',
                    label: __('Selected Items'),
                    collapsible: 0
                },
                {
                    fieldname: 'selected_html',
                    fieldtype: 'HTML',
                    options: '<div class="text-muted text-center" style="padding: 20px;">No items selected yet</div>'
                }
            ],
            primary_action_label: __('Add to Table'),
            primary_action: function() {
                let selected = d.selected_items || {};
                let items_to_add = Object.values(selected);

                if (items_to_add.length === 0) {
                    frappe.msgprint(__('Please select at least one item'));
                    return;
                }

                // Fetch proper prices for all selected items
                let price_list = frm.doc.price_list || undefined;
                let promises = items_to_add.map(function(item) {
                    return frappe.call({
                        method: 'dressup.barcode_label_print.doctype.barcode_label_print.barcode_label_print.get_item_price',
                        args: { item_code: item.item_code, price_list: price_list },
                        async: false
                    });
                });

                Promise.all(promises).then(function(results) {
                    items_to_add.forEach(function(item, idx) {
                        let row = frm.add_child('items');
                        row.item_code = item.item_code;
                        row.item_name = item.item_name;
                        row.qty = item.qty || 1;
                        row.price = results[idx].message ? results[idx].message.price : (item.standard_rate || 0);
                    });

                    frm.refresh_field('items');
                    frm.dirty();
                    d.hide();

                    frappe.show_alert({
                        message: __(`${items_to_add.length} item(s) added successfully`),
                        indicator: 'green'
                    });
                });
            }
        });

        // Initialize selected items store
        d.selected_items = {};

        // Debounced search
        let search_timeout;
        d.fields_dict.search_items.$input.on('input', function() {
            clearTimeout(search_timeout);
            let search_term = $(this).val();
            let item_group = d.get_value('item_group');

            if (!search_term && !item_group) {
                d.fields_dict.results_html.$wrapper.html(
                    '<div class="text-muted text-center" style="padding: 40px;">Type to search for items...</div>'
                );
                return;
            }

            search_timeout = setTimeout(function() {
                let filters = {};
                if (search_term) {
                    filters['name'] = ['like', `%${search_term}%`];
                }
                if (item_group) {
                    filters['item_group'] = item_group;
                }

                frappe.call({
                    method: 'frappe.client.get_list',
                    args: {
                        doctype: 'Item',
                        filters: filters,
                        or_filters: search_term ? {
                            'item_name': ['like', `%${search_term}%`],
                            'name': ['like', `%${search_term}%`]
                        } : undefined,
                        fields: ['name as item_code', 'item_name', 'item_group', 'standard_rate'],
                        limit_page_length: 50,
                        order_by: 'item_name asc'
                    },
                    callback: function(r) {
                        render_search_results(d, r.message || []);
                    }
                });
            }, 300);
        });

        // Render search results
        function render_search_results(dialog, items) {
            if (!items || items.length === 0) {
                dialog.fields_dict.results_html.$wrapper.html(
                    '<div class="text-muted text-center" style="padding: 40px;">No items found</div>'
                );
                return;
            }

            let default_qty = dialog.get_value('default_qty') || 1;
            let html = `
                <div style="max-height: 300px; overflow-y: auto;">
                    <div style="display: flex; align-items: center; padding: 8px 12px; background: var(--subtle-fg); border-bottom: 1px solid var(--border-color); font-weight: 600; font-size: 12px; position: sticky; top: 0; z-index: 1;">
                        <div style="width: 40px; text-align: center;">
                            <input type="checkbox" class="bulk-select-all" title="Select All">
                        </div>
                        <div style="flex: 2;">Item Code</div>
                        <div style="flex: 3;">Item Name</div>
                        <div style="flex: 1.5;">Item Group</div>
                        <div style="flex: 1; text-align: right;">Price</div>
                    </div>
            `;

            items.forEach(function(item) {
                let is_selected = dialog.selected_items[item.item_code] ? 'checked' : '';
                html += `
                    <div class="bulk-item-row" style="display: flex; align-items: center; padding: 8px 12px; border-bottom: 1px solid var(--border-color); cursor: pointer; transition: background 0.15s;" 
                         onmouseover="this.style.background='var(--subtle-fg)'" 
                         onmouseout="this.style.background=''"
                         data-item-code="${frappe.utils.escape_html(item.item_code)}"
                         data-item-name="${frappe.utils.escape_html(item.item_name)}"
                         data-standard-rate="${item.standard_rate || 0}">
                        <div style="width: 40px; text-align: center;">
                            <input type="checkbox" class="bulk-item-check" ${is_selected}>
                        </div>
                        <div style="flex: 2; font-weight: 500; font-size: 13px;">${frappe.utils.escape_html(item.item_code)}</div>
                        <div style="flex: 3; color: var(--text-muted); font-size: 13px;">${frappe.utils.escape_html(item.item_name)}</div>
                        <div style="flex: 1.5; font-size: 12px;">
                            <span style="background: var(--subtle-fg); padding: 2px 8px; border-radius: 10px;">${frappe.utils.escape_html(item.item_group || '')}</span>
                        </div>
                        <div style="flex: 1; text-align: right; font-size: 13px;">${format_currency(item.standard_rate || 0)}</div>
                    </div>
                `;
            });

            html += '</div>';
            html += `<div style="padding: 8px 12px; font-size: 12px; color: var(--text-muted);">${items.length} item(s) found</div>`;

            dialog.fields_dict.results_html.$wrapper.html(html);

            // Click on row to toggle checkbox
            dialog.fields_dict.results_html.$wrapper.find('.bulk-item-row').on('click', function(e) {
                if ($(e.target).is('input[type="checkbox"]')) return;
                let checkbox = $(this).find('.bulk-item-check');
                checkbox.prop('checked', !checkbox.prop('checked'));
                checkbox.trigger('change');
            });

            // Handle checkbox changes
            dialog.fields_dict.results_html.$wrapper.find('.bulk-item-check').on('change', function() {
                let row = $(this).closest('.bulk-item-row');
                let item_code = row.data('item-code');
                let item_name = row.data('item-name');
                let standard_rate = row.data('standard-rate');
                let qty = dialog.get_value('default_qty') || 1;

                if ($(this).prop('checked')) {
                    dialog.selected_items[item_code] = {
                        item_code: item_code,
                        item_name: item_name,
                        standard_rate: standard_rate,
                        qty: qty
                    };
                } else {
                    delete dialog.selected_items[item_code];
                }

                render_selected_items(dialog);
            });

            // Select All checkbox
            dialog.fields_dict.results_html.$wrapper.find('.bulk-select-all').on('change', function() {
                let checked = $(this).prop('checked');
                let qty = dialog.get_value('default_qty') || 1;

                dialog.fields_dict.results_html.$wrapper.find('.bulk-item-check').each(function() {
                    $(this).prop('checked', checked);
                    let row = $(this).closest('.bulk-item-row');
                    let item_code = row.data('item-code');

                    if (checked) {
                        dialog.selected_items[item_code] = {
                            item_code: item_code,
                            item_name: row.data('item-name'),
                            standard_rate: row.data('standard-rate'),
                            qty: qty
                        };
                    } else {
                        delete dialog.selected_items[item_code];
                    }
                });

                render_selected_items(dialog);
            });
        }

        // Render selected items
        function render_selected_items(dialog) {
            let selected = dialog.selected_items;
            let keys = Object.keys(selected);

            if (keys.length === 0) {
                dialog.fields_dict.selected_html.$wrapper.html(
                    '<div class="text-muted text-center" style="padding: 20px;">No items selected yet</div>'
                );
                return;
            }

            let html = `
                <div style="max-height: 200px; overflow-y: auto;">
                    <div style="display: flex; padding: 6px 12px; background: var(--subtle-fg); font-weight: 600; font-size: 12px; border-bottom: 1px solid var(--border-color); position: sticky; top: 0;">
                        <div style="flex: 2;">Item Code</div>
                        <div style="flex: 3;">Item Name</div>
                        <div style="flex: 1; text-align: center;">Print Qty</div>
                        <div style="flex: 1; text-align: right;">Price</div>
                        <div style="width: 40px;"></div>
                    </div>
            `;

            keys.forEach(function(key) {
                let item = selected[key];
                html += `
                    <div class="selected-item-row" style="display: flex; align-items: center; padding: 6px 12px; border-bottom: 1px solid var(--border-color); font-size: 13px;"
                         data-item-code="${frappe.utils.escape_html(item.item_code)}">
                        <div style="flex: 2; font-weight: 500;">${frappe.utils.escape_html(item.item_code)}</div>
                        <div style="flex: 3; color: var(--text-muted);">${frappe.utils.escape_html(item.item_name)}</div>
                        <div style="flex: 1; text-align: center;">
                            <input type="number" class="selected-item-qty form-control input-xs" 
                                   value="${item.qty}" min="1" 
                                   style="width: 60px; text-align: center; display: inline-block; height: 28px;">
                        </div>
                        <div style="flex: 1; text-align: right;">${format_currency(item.standard_rate || 0)}</div>
                        <div style="width: 40px; text-align: center;">
                            <button class="btn btn-xs btn-danger remove-selected-item" title="Remove">✕</button>
                        </div>
                    </div>
                `;
            });

            html += '</div>';
            html += `<div style="padding: 8px 12px; font-weight: 600; font-size: 13px; color: var(--primary);">${keys.length} item(s) selected</div>`;

            dialog.fields_dict.selected_html.$wrapper.html(html);

            // Handle qty change
            dialog.fields_dict.selected_html.$wrapper.find('.selected-item-qty').on('change', function() {
                let item_code = $(this).closest('.selected-item-row').data('item-code');
                let new_qty = parseInt($(this).val()) || 1;
                if (dialog.selected_items[item_code]) {
                    dialog.selected_items[item_code].qty = new_qty;
                }
            });

            // Handle remove
            dialog.fields_dict.selected_html.$wrapper.find('.remove-selected-item').on('click', function() {
                let item_code = $(this).closest('.selected-item-row').data('item-code');
                delete dialog.selected_items[item_code];

                // Uncheck in search results
                dialog.fields_dict.results_html.$wrapper
                    .find(`.bulk-item-row[data-item-code="${item_code}"]`)
                    .find('.bulk-item-check')
                    .prop('checked', false);

                render_selected_items(dialog);
            });
        }

        d.show();

        // Style the dialog
        d.$wrapper.find('.modal-dialog').css('max-width', '900px');
    },

    show_item_group_dialog: function(frm) {
        let d = new frappe.ui.Dialog({
            title: __('Add Items from Item Group'),
            fields: [
                {
                    fieldname: 'item_group',
                    fieldtype: 'Link',
                    label: __('Item Group'),
                    options: 'Item Group',
                    reqd: 1
                },
                {
                    fieldname: 'col1',
                    fieldtype: 'Column Break'
                },
                {
                    fieldname: 'qty',
                    fieldtype: 'Int',
                    label: __('Print Qty (for all)'),
                    default: 1,
                    reqd: 1
                }
            ],
            primary_action_label: __('Add All Items'),
            primary_action: function() {
                let values = d.get_values();
                if (!values) return;

                frappe.call({
                    method: 'dressup.barcode_label_print.doctype.barcode_label_print.barcode_label_print.get_items_by_group',
                    args: {
                        item_group: values.item_group
                    },
                    freeze: true,
                    freeze_message: __('Fetching items...'),
                    callback: function(r) {
                        if (r.message && r.message.length > 0) {
                            let price_list = frm.doc.price_list || undefined;
                            let price_promises = r.message.map(function(item) {
                                return frappe.call({
                                    method: 'dressup.barcode_label_print.doctype.barcode_label_print.barcode_label_print.get_item_price',
                                    args: { item_code: item.item_code, price_list: price_list },
                                    async: false
                                });
                            });

                            let items_data = r.message;
                            let item_group_name = values.item_group;
                            let print_qty = values.qty || 1;

                            Promise.all(price_promises).then(function(price_results) {
                                items_data.forEach(function(item, idx) {
                                    let row = frm.add_child('items');
                                    row.item_code = item.item_code;
                                    row.item_name = item.item_name;
                                    row.qty = print_qty;
                                    row.price = price_results[idx].message ? price_results[idx].message.price : (item.standard_rate || 0);
                                });

                                frm.refresh_field('items');
                                frm.dirty();
                                d.hide();

                                frappe.show_alert({
                                    message: __(`${items_data.length} item(s) added from ${item_group_name}`),
                                    indicator: 'green'
                                });
                            });
                        } else {
                            frappe.msgprint(__('No items found in this Item Group'));
                        }
                    }
                });
            }
        });

        d.show();
    },

    show_serial_no_dialog: function(frm) {
        let d = new frappe.ui.Dialog({
            title: __('Add All Serial Numbers for an Item'),
            fields: [
                {
                    fieldname: 'item_code',
                    fieldtype: 'Link',
                    label: __('Item Code'),
                    options: 'Item',
                    reqd: 1,
                    description: __('Select the item — all its active serial numbers will be added')
                },
                {
                    fieldname: 'col1',
                    fieldtype: 'Column Break'
                },
                {
                    fieldname: 'warehouse',
                    fieldtype: 'Link',
                    label: __('Warehouse'),
                    options: 'Warehouse',
                    description: __('Optional: filter by warehouse')
                },
                {
                    fieldname: 'col2',
                    fieldtype: 'Column Break'
                },
                {
                    fieldname: 'qty',
                    fieldtype: 'Int',
                    label: __('Print Qty (per serial)'),
                    default: 1,
                    description: __('Number of labels per serial number')
                }
            ],
            primary_action_label: __('Add All Serial Nos'),
            primary_action: function() {
                let item_code = d.get_value('item_code');
                let warehouse = d.get_value('warehouse');
                let print_qty = d.get_value('qty') || 1;

                if (!item_code) {
                    frappe.msgprint(__('Please select an Item'));
                    return;
                }

                frappe.call({
                    method: 'dressup.barcode_label_print.doctype.barcode_label_print.barcode_label_print.get_serial_nos_for_item',
                    args: {
                        item_code: item_code,
                        warehouse: warehouse || undefined
                    },
                    freeze: true,
                    freeze_message: __('Fetching serial numbers...'),
                    callback: function(r) {
                        let serials = r.message || [];

                        if (serials.length === 0) {
                            frappe.msgprint(__('No active serial numbers found for {0}', [item_code]));
                            return;
                        }

                        // Fetch item details and price
                        let price_list = frm.doc.price_list || undefined;
                        frappe.db.get_value('Item', item_code, ['item_name'], function(item_r) {
                            frappe.call({
                                method: 'dressup.barcode_label_print.doctype.barcode_label_print.barcode_label_print.get_item_price',
                                args: { item_code: item_code, price_list: price_list },
                                callback: function(price_r) {
                                    let fetched_price = price_r.message ? price_r.message.price : 0;
                                    serials.forEach(function(sn) {
                                        let row = frm.add_child('items');
                                        row.item_code = item_code;
                                        row.item_name = item_r ? item_r.item_name : '';
                                        row.serial_no = sn.serial_no;
                                        row.batch_no = sn.batch_no || '';
                                        row.qty = print_qty;
                                        row.price = fetched_price;
                                    });

                                    frm.refresh_field('items');
                                    frm.dirty();
                                    d.hide();

                                    frappe.show_alert({
                                        message: __(`${serials.length} serial number(s) added for ${item_code}`),
                                        indicator: 'green'
                                    });
                                }
                            });
                        });
                    }
                });
            }
        });

        d.show();
    },

    setup: function(frm) {
        frm.set_query('color_attribute', 'items', function(doc, cdt, cdn) {
            let row = locals[cdt][cdn];
            if (row.item_code) {
                return {
                    query: "dressup.barcode_label_print.doctype.barcode_label_print.barcode_label_print.get_item_attributes_query",
                    filters: { item_code: row.item_code }
                };
            }
        });
        
        frm.set_query('size_attribute', 'items', function(doc, cdt, cdn) {
            let row = locals[cdt][cdn];
            if (row.item_code) {
                return {
                    query: "dressup.barcode_label_print.doctype.barcode_label_print.barcode_label_print.get_item_attributes_query",
                    filters: { item_code: row.item_code }
                };
            }
        });
    }
});

frappe.ui.form.on('Barcode Label Item', {

    item_code: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.item_code) {
            // Fetch item name
            frappe.db.get_value('Item', row.item_code, ['item_name'], function(r) {
                if (r) {
                    frappe.model.set_value(cdt, cdn, 'item_name', r.item_name);
                }
            });
            // Fetch price: Item Price (Price List) > Valuation Rate > Standard Rate
            let price_list = frm.doc.price_list || undefined;
            frappe.call({
                method: 'dressup.barcode_label_print.doctype.barcode_label_print.barcode_label_print.get_item_price',
                args: {
                    item_code: row.item_code,
                    price_list: price_list
                },
                callback: function(r) {
                    if (r.message) {
                        frappe.model.set_value(cdt, cdn, 'price', r.message.price);
                    }
                }
            });
            
            // Auto fetch attributes
            frappe.call({
                method: 'dressup.barcode_label_print.doctype.barcode_label_print.barcode_label_print.get_item_attributes_data',
                args: { item_code: row.item_code },
                callback: function(r) {
                    if (r.message) {
                        let color_set = false;
                        let size_set = false;
                        r.message.forEach(function(attr) {
                            if (!color_set && attr.attribute.toLowerCase().includes('color')) {
                                frappe.model.set_value(cdt, cdn, 'color_attribute', attr.attribute);
                                frappe.model.set_value(cdt, cdn, 'color', attr.attribute_value);
                                color_set = true;
                            }
                            if (!size_set && attr.attribute.toLowerCase().includes('size')) {
                                frappe.model.set_value(cdt, cdn, 'size_attribute', attr.attribute);
                                frappe.model.set_value(cdt, cdn, 'size', attr.attribute_value);
                                size_set = true;
                            }
                        });
                    }
                }
            });
        }
    },

    color_attribute: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.item_code && row.color_attribute) {
            frappe.call({
                method: 'dressup.barcode_label_print.doctype.barcode_label_print.barcode_label_print.get_item_attributes_data',
                args: { item_code: row.item_code },
                callback: function(r) {
                    if (r.message) {
                        let attr = r.message.find(a => a.attribute === row.color_attribute);
                        if (attr) frappe.model.set_value(cdt, cdn, 'color', attr.attribute_value);
                    }
                }
            });
        } else if (!row.color_attribute) {
            frappe.model.set_value(cdt, cdn, 'color', '');
        }
    },

    size_attribute: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.item_code && row.size_attribute) {
            frappe.call({
                method: 'dressup.barcode_label_print.doctype.barcode_label_print.barcode_label_print.get_item_attributes_data',
                args: { item_code: row.item_code },
                callback: function(r) {
                    if (r.message) {
                        let attr = r.message.find(a => a.attribute === row.size_attribute);
                        if (attr) frappe.model.set_value(cdt, cdn, 'size', attr.attribute_value);
                    }
                }
            });
        } else if (!row.size_attribute) {
            frappe.model.set_value(cdt, cdn, 'size', '');
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
