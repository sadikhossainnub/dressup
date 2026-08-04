frappe.ui.form.on('Barcode Label Template', {
    refresh: function (frm) {
        setup_designer(frm);
    },
    designer_mode: function (frm) {
        setup_designer(frm);
    },
    label_width: function (frm) {
        if (frm.designer_instance) frm.designer_instance.renderCanvas();
    },
    label_height: function (frm) {
        if (frm.designer_instance) frm.designer_instance.renderCanvas();
    }
});

function setup_designer(frm) {
    if (frm.doc.designer_mode !== 'Custom Drag & Drop') {
        if (frm.fields_dict.designer_html) {
            frm.fields_dict.designer_html.$wrapper.empty();
        }
        return;
    }

    const wrapper = frm.fields_dict.designer_html.$wrapper;
    wrapper.empty();

    const designer = new LabelDesigner(frm, wrapper);
    frm.designer_instance = designer;
    designer.init();
}

class LabelDesigner {
    constructor(frm, wrapper) {
        this.frm = frm;
        this.wrapper = wrapper;
        this.scale = 4; // 1mm = 4px
        this.selectedId = null;

        // Parse initial layout JSON or load default template
        this.elements = [];
        try {
            if (this.frm.doc.custom_layout_json) {
                this.elements = JSON.parse(this.frm.doc.custom_layout_json);
            }
        } catch (e) {
            this.elements = [];
        }

        if (!Array.isArray(this.elements) || this.elements.length === 0) {
            this.elements = this.getDefaultElements();
        }
    }

    getDefaultElements() {
        return [
            { id: 'el_qr', type: 'qr_code', label: 'QR Code', x: 2, y: 2, w: 18, h: 18, fontSize: 10, style: 'Normal', align: 'center' },
            { id: 'el_name', type: 'item_name', label: 'Item Name', x: 22, y: 2, w: 25, h: 6, fontSize: 8, style: 'Bold', align: 'left' },
            { id: 'el_size', type: 'size', label: 'Size', x: 22, y: 9, w: 12, h: 5, fontSize: 7, style: 'Normal', align: 'left' },
            { id: 'el_color', type: 'color', label: 'Color', x: 35, y: 9, w: 12, h: 5, fontSize: 7, style: 'Normal', align: 'left' },
            { id: 'el_price', type: 'price', label: 'Price with VAT', x: 22, y: 15, w: 25, h: 6, fontSize: 9, style: 'Bold', align: 'left' }
        ];
    }

    init() {
        this.renderContainer();
        this.renderCanvas();
        this.renderElements();
        this.saveToDoc();
    }

    renderContainer() {
        this.wrapper.html(`
            <style>
                .designer-wrapper { display: flex; gap: 15px; background: #f7f9fb; padding: 15px; border-radius: 8px; border: 1px solid #d1d8dd; }
                .designer-toolbox { width: 180px; display: flex; flex-direction: column; gap: 8px; }
                .designer-toolbox button { width: 100%; text-align: left; background: #fff; border: 1px solid #d1d8dd; border-radius: 4px; padding: 6px 10px; font-size: 12px; cursor: pointer; }
                .designer-toolbox button:hover { background: #eef3f7; border-color: #2490ef; }
                .designer-canvas-area { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: flex-start; overflow: auto; background: #e0e5eb; padding: 20px; border-radius: 6px; }
                .designer-canvas { position: relative; background: #ffffff; border: 2px solid #333; box-shadow: 0 4px 10px rgba(0,0,0,0.15); box-sizing: content-box; }
                .designer-props { width: 220px; background: #fff; border: 1px solid #d1d8dd; border-radius: 6px; padding: 12px; font-size: 12px; }
                .designer-el { position: absolute; border: 1px dashed #888; box-sizing: border-box; cursor: move; user-select: none; display: flex; align-items: center; justify-content: center; padding: 2px; overflow: hidden; font-size: 11px; background: rgba(255,255,255,0.85); }
                .designer-el.selected { border: 2px solid #2490ef; z-index: 10; background: rgba(36,144,239,0.08); }
                .designer-el-qr { background: #eee; font-weight: bold; font-size: 10px; text-align: center; }
                .designer-el-barcode { background: #e8e8e8; font-family: monospace; font-size: 9px; }
                .designer-props label { display: block; margin-top: 8px; margin-bottom: 2px; font-weight: 600; color: #555; }
                .designer-props input, .designer-props select { width: 100%; padding: 4px 6px; font-size: 12px; border: 1px solid #ccc; border-radius: 4px; }
            </style>
            <div class="designer-wrapper">
                <div class="designer-toolbox">
                    <h6 style="margin: 0 0 5px 0; font-weight: bold; color: #333;">Add Elements</h6>
                    <button data-type="qr_code">+ QR Code</button>
                    <button data-type="barcode">+ Barcode</button>
                    <button data-type="item_code">+ Item Code</button>
                    <button data-type="item_name">+ Item Name</button>
                    <button data-type="size">+ Size</button>
                    <button data-type="color">+ Color</button>
                    <button data-type="price">+ Price</button>
                    <button data-type="batch_no">+ Batch No</button>
                    <button data-type="serial_no">+ Serial No</button>
                    <button data-type="static_text">+ Text</button>
                </div>
                <div class="designer-canvas-area">
                    <div style="margin-bottom: 8px; font-size: 11px; color: #666; font-weight: 500;">
                        Label Canvas (${this.frm.doc.label_width || 50}mm × ${this.frm.doc.label_height || 25}mm)
                    </div>
                    <div class="designer-canvas" id="label-canvas"></div>
                </div>
                <div class="designer-props" id="designer-props-panel">
                    <h6 style="margin: 0 0 10px 0; font-weight: bold; color: #333;">Element Properties</h6>
                    <div id="props-content" style="color: #888;">Select an element to edit properties.</div>
                </div>
            </div>
        `);

        // Attach Toolbox click handlers
        this.wrapper.find('.designer-toolbox button').on('click', (e) => {
            const type = $(e.currentTarget).data('type');
            this.addElement(type);
        });

        // Click outside canvas to deselect
        this.wrapper.find('.designer-canvas-area').on('click', (e) => {
            if ($(e.target).hasClass('designer-canvas-area') || $(e.target).hasClass('designer-canvas')) {
                this.selectElement(null);
            }
        });
    }

    renderCanvas() {
        const w = (this.frm.doc.label_width || 50) * this.scale;
        const h = (this.frm.doc.label_height || 25) * this.scale;
        const canvas = this.wrapper.find('#label-canvas');
        canvas.css({ width: w + 'px', height: h + 'px' });
    }

    renderElements() {
        const canvas = this.wrapper.find('#label-canvas');
        canvas.empty();

        this.elements.forEach(el => {
            const $el = $(`<div class="designer-el ${el.id === this.selectedId ? 'selected' : ''}" id="${el.id}"></div>`);

            // Position and size in px
            $el.css({
                left: (el.x * this.scale) + 'px',
                top: (el.y * this.scale) + 'px',
                width: (el.w * this.scale) + 'px',
                height: (el.h * this.scale) + 'px',
                fontSize: (el.fontSize || 8) + 'pt',
                textAlign: el.align || 'left'
            });

            if (el.style === 'Bold') $el.css({ fontWeight: 'bold' });
            if (el.style === 'Italic') $el.css({ fontStyle: 'italic' });
            if (el.style === 'Bold Italic') $el.css({ fontWeight: 'bold', fontStyle: 'italic' });

            // Content preview
            if (el.type === 'qr_code') {
                $el.addClass('designer-el-qr').html('<span>[QR Code]</span>');
            } else if (el.type === 'barcode') {
                $el.addClass('designer-el-barcode').html('<span>||||||||||||||</span>');
            } else {
                $el.text(el.label || el.type);
            }

            // Click selection
            $el.on('click', (e) => {
                e.stopPropagation();
                this.selectElement(el.id);
            });

            // Dragging logic
            this.makeDraggable($el, el);

            canvas.append($el);
        });
    }

    makeDraggable($el, el) {
        let isDragging = false;
        let startX, startY, origX, origY;

        $el.on('mousedown', (e) => {
            isDragging = true;
            startX = e.clientX;
            startY = e.clientY;
            origX = el.x;
            origY = el.y;

            this.selectElement(el.id);

            const onMouseMove = (me) => {
                if (!isDragging) return;
                const dx = (me.clientX - startX) / this.scale;
                const dy = (me.clientY - startY) / this.scale;

                // Round to 0.5mm grid
                let newX = Math.max(0, Math.round((origX + dx) * 2) / 2);
                let newY = Math.max(0, Math.round((origY + dy) * 2) / 2);

                const maxW = (this.frm.doc.label_width || 50) - el.w;
                const maxH = (this.frm.doc.label_height || 25) - el.h;
                newX = Math.min(newX, maxW);
                newY = Math.min(newY, maxH);

                el.x = newX;
                el.y = newY;

                $el.css({
                    left: (newX * this.scale) + 'px',
                    top: (newY * this.scale) + 'px'
                });

                this.updatePropsPanel();
            };

            const onMouseUp = () => {
                if (isDragging) {
                    isDragging = false;
                    $(document).off('mousemove', onMouseMove);
                    $(document).off('mouseup', onMouseUp);
                    this.saveToDoc();
                }
            };

            $(document).on('mousemove', onMouseMove);
            $(document).on('mouseup', onMouseUp);
        });
    }

    addElement(type) {
        const typeLabels = {
            qr_code: 'QR Code',
            barcode: 'Barcode',
            item_code: 'Item Code',
            item_name: 'Item Name',
            size: 'Size',
            color: 'Color',
            price: 'Price',
            batch_no: 'Batch No',
            serial_no: 'Serial No',
            static_text: 'Custom Text'
        };

        const newId = 'el_' + Date.now();
        const defaultW = (type === 'qr_code' || type === 'barcode') ? 15 : 20;
        const defaultH = (type === 'qr_code') ? 15 : (type === 'barcode' ? 8 : 5);

        const newEl = {
            id: newId,
            type: type,
            label: typeLabels[type] || type,
            x: 2,
            y: 2,
            w: defaultW,
            h: defaultH,
            fontSize: 8,
            style: 'Normal',
            align: 'left'
        };

        this.elements.push(newEl);
        this.selectElement(newId);
        this.renderElements();
        this.saveToDoc();
    }

    selectElement(id) {
        this.selectedId = id;
        this.wrapper.find('.designer-el').removeClass('selected');
        if (id) {
            this.wrapper.find(`#${id}`).addClass('selected');
        }
        this.updatePropsPanel();
    }

    updatePropsPanel() {
        const panel = this.wrapper.find('#props-content');
        if (!this.selectedId) {
            panel.html('<div style="color: #888;">Select an element on canvas to edit properties.</div>');
            return;
        }

        const el = this.elements.find(e => e.id === this.selectedId);
        if (!el) return;

        panel.html(`
            <label>Type / Field</label>
            <input type="text" value="${el.label || el.type}" disabled />

            <label>X Position (mm)</label>
            <input type="number" id="prop-x" value="${el.x}" step="0.5" />

            <label>Y Position (mm)</label>
            <input type="number" id="prop-y" value="${el.y}" step="0.5" />

            <label>Width (mm)</label>
            <input type="number" id="prop-w" value="${el.w}" step="0.5" />

            <label>Height (mm)</label>
            <input type="number" id="prop-h" value="${el.h}" step="0.5" />

            <label>Font Size (pt)</label>
            <input type="number" id="prop-font-size" value="${el.fontSize || 8}" min="4" max="72" />

            <label>Font Style</label>
            <select id="prop-style">
                <option value="Normal" ${el.style === 'Normal' ? 'selected' : ''}>Normal</option>
                <option value="Bold" ${el.style === 'Bold' ? 'selected' : ''}>Bold</option>
                <option value="Italic" ${el.style === 'Italic' ? 'selected' : ''}>Italic</option>
                <option value="Bold Italic" ${el.style === 'Bold Italic' ? 'selected' : ''}>Bold Italic</option>
            </select>

            <label>Alignment</label>
            <select id="prop-align">
                <option value="left" ${el.align === 'left' ? 'selected' : ''}>Left</option>
                <option value="center" ${el.align === 'center' ? 'selected' : ''}>Center</option>
                <option value="right" ${el.align === 'right' ? 'selected' : ''}>Right</option>
            </select>

            <button id="btn-delete-el" class="btn btn-danger btn-xs" style="margin-top: 15px; width: 100%;">
                Delete Element
            </button>
        `);

        // Attach property change events
        panel.find('input, select').on('change input', () => {
            el.x = parseFloat(panel.find('#prop-x').val()) || 0;
            el.y = parseFloat(panel.find('#prop-y').val()) || 0;
            el.w = parseFloat(panel.find('#prop-w').val()) || 5;
            el.h = parseFloat(panel.find('#prop-h').val()) || 5;
            el.fontSize = parseInt(panel.find('#prop-font-size').val()) || 8;
            el.style = panel.find('#prop-style').val();
            el.align = panel.find('#prop-align').val();

            this.renderElements();
            this.saveToDoc();
        });

        panel.find('#btn-delete-el').on('click', () => {
            this.elements = this.elements.filter(e => e.id !== this.selectedId);
            this.selectedId = null;
            this.renderElements();
            this.updatePropsPanel();
            this.saveToDoc();
        });
    }

    saveToDoc() {
        const jsonStr = JSON.stringify(this.elements, null, 2);
        this.frm.set_value('custom_layout_json', jsonStr);
    }
}
