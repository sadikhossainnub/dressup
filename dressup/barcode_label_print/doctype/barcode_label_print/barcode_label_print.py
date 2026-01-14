# Copyright (c) 2024, Prime Technology of Bangladesh and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from dressup.barcode_label_print.utils import get_barcode_base64

class BarcodeLabelPrint(Document):
	def validate(self):
		self.generate_preview()

	def generate_preview(self):
		if not self.label_template or not self.items:
			self.preview_html = ""
			return

		template = frappe.get_doc("Barcode Label Template", self.label_template)
		
		# Prepare data for all items
		items_data = []
		for item in self.items:
			# Determine code value
			code_value = item.item_code
			if item.batch_no:
				code_value = item.batch_no
			if item.serial_no:
				code_value = item.serial_no
				
			barcode_image = get_barcode_base64(template.barcode_type, code_value)
			
			qty = item.qty if item.qty > 0 else 1
			for _ in range(qty):
				items_data.append({
					"item_code": item.item_code,
					"item_name": item.item_name,
					"batch_no": item.batch_no,
					"serial_no": item.serial_no,
					"price": item.price,
					"expiry_date": item.expiry_date,
					"company": frappe.defaults.get_user_default("Company"),
					"barcode_image": barcode_image
				})

		# Layout calculations
		labels_per_row = template.labels_per_row if template.labels_per_row > 0 else 1
		horizontal_gap = template.horizontal_gap or 0
		vertical_gap = template.vertical_gap or 0
		
		# HTML Construction
		html = f"""
		<div style="
			display: flex;
			flex-wrap: wrap;
			gap: {vertical_gap}mm {horizontal_gap}mm;
			padding-top: {template.top_margin or 0}mm;
			padding-left: {template.left_margin or 0}mm;
		">
		"""
		
		# Check for Visual Design Data
		import json
		design_elements = []
		if template.design_data:
			try:
				design_elements = json.loads(template.design_data)
			except:
				pass

		for data in items_data:
			# If we have a visual design, use absolute positioning
			if design_elements:
				label_html = f"""
				<div style="
					width: {template.label_width}mm;
					height: {template.label_height}mm;
					position: relative;
					border: 1px dotted #ccc;
					box-sizing: border-box;
					background: white;
					overflow: hidden;
					page-break-inside: avoid;
				">
				"""
				# Scale factor (designer uses px, print uses mm or px)
				# NOTE: The designer saves in PX based on 96 DPI (approx 3.78 px/mm)
				# We will render in PX to match the design exactly
				
				for el in design_elements:
					content = el.get("content", "")
					
					# Dynamic Data Binding
					if el.get("type") == "field":
						field_name = el.get("content")
						if field_name == "price":
							content = frappe.format_value(data.get("price"), {"fieldtype": "Currency"})
						else:
							content = data.get(field_name, "")
							
					elif el.get("type") == "barcode":
						if data.get("barcode_image"):
							content = f"<img src='{data['barcode_image']}' style='width: 100%; height: 100%;' />"
						else:
							content = ""
							
					# Styles
					style = f"""
						position: absolute;
						left: {el.get('x')}px;
						top: {el.get('y')}px;
						width: {el.get('width')}px;
						height: {el.get('height')}px;
						font-size: {el.get('fontSize')}px;
						font-weight: {'bold' if el.get('bold') else 'normal'};
						text-align: {el.get('align', 'left')};
						white-space: nowrap;
						overflow: hidden;
					"""
					
					label_html += f"<div style='{style}'>{content}</div>"

				label_html += "</div>"
				
			else:
				# Fallback to Old Flex Layout
				label_html = f"""
				<div style="
					width: {template.label_width}mm;
					height: {template.label_height}mm;
					border: 1px dotted #ccc; /* Dotted border for preview only */
					box-sizing: border-box;
					padding: 2mm;
					font-family: sans-serif;
					font-size: {template.font_size}px;
					display: flex;
					flex-direction: column;
					align-items: center;
					justify-content: center;
					text-align: center;
					overflow: hidden;
					background: white;
					page-break-inside: avoid;
				">
				"""
				
				if template.include_company_name and data.get("company"):
					label_html += f"<div style='font-weight: bold;'>{data['company']}</div>"
					
				if template.include_item_name and data.get("item_name"):
					label_html += f"<div style='margin-bottom: 2px; line-height: 1.1;'>{data['item_name']}</div>"
					
				if template.include_item_code and data.get("item_code"):
					label_html += f"<div>{data['item_code']}</div>"
					
				if template.get("include_price") and data.get("price"):
					label_html += f"<div style='font-weight: bold; font-size: 1.1em;'>{frappe.format_value(data['price'], {'fieldtype': 'Currency'})}</div>"
					
				if data.get("barcode_image"):
					label_html += f"<img src='{data['barcode_image']}' style='max-width: 100%; max-height: 40%; margin: 2px 0;' />"
				
				if template.include_batch_no and data.get("batch_no"):
					label_html += f"<div style='font-size: 0.9em;'>Batch: {data['batch_no']}</div>"
					
				if template.include_serial_no and data.get("serial_no"):
					label_html += f"<div style='font-size: 0.9em;'>SN: {data['serial_no']}</div>"
					
				if template.include_expiry_date and data.get("expiry_date"):
					label_html += f"<div style='font-size: 0.9em;'>Exp: {data['expiry_date']}</div>"
					
				label_html += "</div>"
			
			html += label_html
			
		html += "</div>"
		
		# Simple breakdown handling for rendering, but CSS flex gap handles it visually.
		# For print formats, page breaks might be needed.
		
		self.preview_html = html
