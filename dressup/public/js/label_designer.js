
class LabelDesigner {
    constructor(wrapper, options) {
        this.wrapper = wrapper;
        this.options = options || {};
        this.elements = [];
        this.scale = 3.78; // approx px per mm (96 DPI / 25.4)
        this.width = (this.options.width || 50) * this.scale;
        this.height = (this.options.height || 25) * this.scale;
        this.data = this.options.data || [];
        this.readOnly = this.options.readOnly || false;

        this.setup_ui();
        this.load_data(this.data);
    }

    setup_ui() {
        this.container = document.createElement('div');
        this.container.className = 'label-designer-container';
        this.container.style.display = 'flex';
        this.container.style.height = '600px';
        this.container.style.border = '1px solid #d1d8dd';
        this.container.style.backgroundColor = '#f4f5f6';

        // Toolbox
        this.toolbox = document.createElement('div');
        this.toolbox.className = 'label-designer-toolbox';
        this.toolbox.style.width = '200px';
        this.toolbox.style.backgroundColor = '#fff';
        this.toolbox.style.borderRight = '1px solid #d1d8dd';
        this.toolbox.style.padding = '10px';

        let toolbox_html = `
            <div style="font-weight: bold; margin-bottom: 10px;">Tools</div>
            <button class="btn btn-default btn-block btn-sm mb-2 btn-add-text">Add Text</button>
            <button class="btn btn-default btn-block btn-sm mb-2 btn-add-field">Add Data Field</button>
            <button class="btn btn-default btn-block btn-sm mb-2 btn-add-barcode">Add Barcode</button>
            <button class="btn btn-default btn-block btn-sm mb-2 btn-add-image">Add Image</button>
            <div style="margin-top: 20px; font-weight: bold;">Properties</div>
            <div id="prop-editor">Select an element</div>
        `;
        this.toolbox.innerHTML = toolbox_html;

        // Bind events
        this.toolbox.querySelector('.btn-add-text').addEventListener('click', () => this.add_element('text'));
        this.toolbox.querySelector('.btn-add-field').addEventListener('click', () => this.add_element('field'));
        this.toolbox.querySelector('.btn-add-barcode').addEventListener('click', () => this.add_element('barcode'));
        this.toolbox.querySelector('.btn-add-image').addEventListener('click', () => this.add_element('image'));

        // Canvas Area
        this.canvasArea = document.createElement('div');
        this.canvasArea.className = 'label-designer-canvas-area';
        this.canvasArea.style.flex = '1';
        this.canvasArea.style.display = 'flex';
        this.canvasArea.style.alignItems = 'center';
        this.canvasArea.style.justifyContent = 'center';
        this.canvasArea.style.overflow = 'auto';

        // The Actual Label
        this.canvas = document.createElement('div');
        this.canvas.className = 'label-canvas';
        this.canvas.style.position = 'relative';
        this.canvas.style.width = this.width + 'px';
        this.canvas.style.height = this.height + 'px';
        this.canvas.style.backgroundColor = 'white';
        this.canvas.style.boxShadow = '0 0 5px rgba(0,0,0,0.1)';
        this.canvas.style.border = '1px solid #000';

        this.canvasArea.appendChild(this.canvas);
        this.container.appendChild(this.toolbox);
        this.container.appendChild(this.canvasArea);
        this.wrapper.appendChild(this.container);

        // Global reference for onclick handlers (a bit hacky but works in this context)
        window.cur_designer = this;
    }

    update_canvas_size(width_mm, height_mm) {
        this.width = width_mm * this.scale;
        this.height = height_mm * this.scale;
        this.canvas.style.width = this.width + 'px';
        this.canvas.style.height = this.height + 'px';
    }

    add_element(type, config) {
        const id = 'el_' + Math.random().toString(36).substr(2, 9);
        const el = {
            id: id,
            type: type,
            x: 10,
            y: 10,
            width: type === 'barcode' ? 150 : 100,
            height: type === 'barcode' ? 50 : 20,
            content: type === 'text' ? 'Text' : (type === 'field' ? 'item_code' : ''),
            fontSize: 12,
            bold: false,
            align: 'left',
            ...config
        };
        this.elements.push(el);
        this.render_element(el);
        this.select_element(id);
        this.save_state();
    }

    render_element(elData) {
        let elDiv = document.getElementById(elData.id);
        if (!elDiv) {
            elDiv = document.createElement('div');
            elDiv.id = elData.id;
            elDiv.style.position = 'absolute';
            elDiv.style.cursor = 'move';
            elDiv.style.border = '1px dashed transparent';
            elDiv.style.boxSizing = 'border-box';

            // Interaction Handles
            elDiv.addEventListener('mousedown', (e) => this.handle_drag_start(e, elData));
            elDiv.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                this.select_element(elData.id);
            });

            this.canvas.appendChild(elDiv);
        }

        // Apply Styles
        elDiv.style.left = elData.x + 'px';
        elDiv.style.top = elData.y + 'px';
        elDiv.style.width = elData.width + 'px';
        elDiv.style.height = elData.height + 'px';
        elDiv.style.fontSize = elData.fontSize + 'px';
        elDiv.style.fontWeight = elData.bold ? 'bold' : 'normal';
        elDiv.style.textAlign = elData.align;

        // Content
        if (elData.type === 'text') {
            elDiv.textContent = elData.content;
            elDiv.style.backgroundColor = 'transparent';
        } else if (elData.type === 'field') {
            elDiv.textContent = '{' + elData.content + '}';
            elDiv.style.backgroundColor = '#e8f0fe';
            elDiv.style.border = '1px solid #b3d7ff';
        } else if (elData.type === 'barcode') {
            elDiv.innerHTML = '<div style="width:100%; height:100%; background: repeating-linear-gradient(90deg, #000 0px, #000 2px, #fff 2px, #fff 4px);"></div>';
            elDiv.style.backgroundColor = '#fafafa';
        } else if (elData.type === 'image') {
            elDiv.textContent = 'IMAGE';
            elDiv.style.backgroundColor = '#eee';
            elDiv.style.display = 'flex';
            elDiv.style.alignItems = 'center';
            elDiv.style.justifyContent = 'center';
        }

        // Selection Highlight
        if (this.selectedId === elData.id) {
            elDiv.style.border = '1px dashed #007bff';
        } else {
            elDiv.style.border = '1px dashed transparent';
        }
    }

    select_element(id) {
        this.selectedId = id;
        this.elements.forEach(el => this.render_element(el));
        this.show_properties(id);
    }

    show_properties(id) {
        const el = this.elements.find(e => e.id === id);
        const propDiv = document.getElementById('prop-editor');
        if (!el || !propDiv) return;

        propDiv.innerHTML = ''; // Clear

        const create_input = (label, type, value, prop, options = {}) => {
            const group = document.createElement('div');
            group.className = 'form-group';
            group.style.marginBottom = '10px';

            const labelEl = document.createElement('label');
            labelEl.textContent = label;
            labelEl.style.fontSize = '12px';
            group.appendChild(labelEl);

            let input;
            if (type === 'select') {
                input = document.createElement('select');
                options.items.forEach(item => {
                    const opt = document.createElement('option');
                    opt.value = item;
                    opt.textContent = item.charAt(0).toUpperCase() + item.slice(1);
                    if (item === value) opt.selected = true;
                    input.appendChild(opt);
                });
            } else if (type === 'checkbox') {
                input = document.createElement('input');
                input.type = 'checkbox';
                input.checked = value;
            } else {
                input = document.createElement('input');
                input.type = type;
                input.value = value;
            }

            input.className = type === 'checkbox' ? '' : 'form-control input-sm';
            input.addEventListener('change', (e) => {
                let val = type === 'checkbox' ? e.target.checked : e.target.value;
                this.update_property(id, prop, val);
            });

            group.appendChild(input);
            return group;
        };

        propDiv.appendChild(create_input('X (px)', 'number', el.x, 'x'));
        propDiv.appendChild(create_input('Y (px)', 'number', el.y, 'y'));
        propDiv.appendChild(create_input('Width (px)', 'number', el.width, 'width'));
        propDiv.appendChild(create_input('Height (px)', 'number', el.height, 'height'));
        propDiv.appendChild(create_input('Font Size', 'number', el.fontSize, 'fontSize'));
        propDiv.appendChild(create_input('Bold', 'checkbox', el.bold, 'bold'));
        propDiv.appendChild(create_input('Text Align', 'select', el.align, 'align', { items: ['left', 'center', 'right'] }));

        if (el.type === 'text' || el.type === 'field') {
            propDiv.appendChild(create_input(el.type === 'field' ? 'Field Name' : 'Content', 'text', el.content, 'content'));
            if (el.type === 'field') {
                const hint = document.createElement('small');
                hint.className = 'text-muted';
                hint.textContent = 'Fields: item_code, item_name, price, batch_no, serial_no, expiry_date';
                propDiv.appendChild(hint);
            }
        }

        const btnRemove = document.createElement('button');
        btnRemove.className = 'btn btn-danger btn-xs mt-3';
        btnRemove.style.width = '100%';
        btnRemove.textContent = 'Remove Element';
        btnRemove.onclick = () => this.remove_element(id);
        propDiv.appendChild(btnRemove);
    }

    update_property(id, prop, value) {
        const el = this.elements.find(e => e.id === id);
        if (el) {
            if (prop === 'x' || prop === 'y' || prop === 'width' || prop === 'height' || prop === 'fontSize') {
                value = parseInt(value);
            }
            el[prop] = value;
            this.render_element(el);
            this.save_state();
        }
    }

    remove_element(id) {
        this.elements = this.elements.filter(e => e.id !== id);
        this.selectedId = null;

        const elDiv = document.getElementById(id);
        if (elDiv) elDiv.remove();

        document.getElementById('prop-editor').innerHTML = 'Select an element';
        this.save_state();
    }

    handle_drag_start(e, elData) {
        if (e.target !== e.currentTarget) return; // Prevent dragging when clicking child controls if any

        const startX = e.clientX;
        const startY = e.clientY;
        const startLeft = elData.x;
        const startTop = elData.y;

        const onMouseMove = (moveEvent) => {
            const dx = moveEvent.clientX - startX;
            const dy = moveEvent.clientY - startY;

            elData.x = startLeft + dx;
            elData.y = startTop + dy;

            // Snap to grid (optional 5px)
            elData.x = Math.round(elData.x / 5) * 5;
            elData.y = Math.round(elData.y / 5) * 5;

            this.render_element(elData);
            this.show_properties(elData.id); // Update props panel live
        };

        const onMouseUp = () => {
            document.removeEventListener('mousemove', onMouseMove);
            document.removeEventListener('mouseup', onMouseUp);
            this.save_state();
        };

        document.addEventListener('mousemove', onMouseMove);
        document.addEventListener('mouseup', onMouseUp);
    }

    save_state() {
        if (this.options.on_save) {
            this.options.on_save(this.elements);
        }
    }

    load_data(data) {
        this.elements = data || [];
        this.canvas.innerHTML = ''; // clear
        this.elements.forEach(el => this.render_element(el));
    }
}

// Attach to window so we can instantiate it
window.LabelDesigner = LabelDesigner;
