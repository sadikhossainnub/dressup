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
		
		# Use simple layout (visual designer removed)
		design_elements = []

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
				# Fallback to Simple Layout with all checkbox options
				label_html = f"""
				<div style="
					width: {template.label_width}mm;
					height: {template.label_height}mm;
					box-sizing: border-box;
					padding: 2mm;
					font-family: Arial, sans-serif;
					font-size: {template.font_size}px;
					overflow: hidden;
					background: white;
					page-break-inside: avoid;
					border: 1px solid #000;
					display: flex;
					flex-direction: column;
					justify-content: space-between;
				">
				"""
				
				# Company Name (Top)
				if template.include_company_name and data.get("company"):
					label_html += f"""
						<div style="
							text-align: center;
							font-weight: bold;
							font-size: {template.font_size * 1.1}px;
							border-bottom: 1px solid #ccc;
							padding-bottom: 1mm;
							margin-bottom: 1mm;
						">{data['company']}</div>
					"""
				
				# Item Name
				if template.include_item_name and data.get("item_name"):
					label_html += f"""
						<div style="
							text-align: center;
							font-size: {template.font_size}px;
							margin-bottom: 1mm;
							overflow: hidden;
							text-overflow: ellipsis;
							white-space: nowrap;
						">{data['item_name']}</div>
					"""
				
				# Item Code
				if template.include_item_code and data.get("item_code"):
					label_html += f"""
						<div style="
							text-align: center;
							font-size: {template.font_size * 0.8}px;
							color: #555;
							margin-bottom: 1mm;
						">{data['item_code']}</div>
					"""
				
				# Batch No
				if template.include_batch_no and data.get("batch_no"):
					label_html += f"""
						<div style="
							text-align: center;
							font-size: {template.font_size * 0.8}px;
							color: #555;
						">Batch: {data['batch_no']}</div>
					"""
				
				# Serial No
				if template.include_serial_no and data.get("serial_no"):
					label_html += f"""
						<div style="
							text-align: center;
							font-size: {template.font_size * 0.8}px;
							color: #555;
						">S/N: {data['serial_no']}</div>
					"""
				
				# Expiry Date
				if template.include_expiry_date and data.get("expiry_date"):
					label_html += f"""
						<div style="
							text-align: center;
							font-size: {template.font_size * 0.8}px;
							color: #555;
						">Exp: {data['expiry_date']}</div>
					"""
				
				# Price
				if template.include_price and data.get("price"):
					price_val = frappe.format_value(data['price'], {'fieldtype': 'Currency'})
					label_html += f"""
						<div style="
							text-align: center;
							font-weight: bold;
							font-size: {template.font_size * 1.2}px;
							margin: 1mm 0;
						">{price_val}</div>
					"""
				
				# Barcode (always at bottom)
				if data.get("barcode_image"):
					label_html += f"""
						<div style="
							text-align: center;
							flex-grow: 1;
							display: flex;
							align-items: center;
							justify-content: center;
						">
							<img src='{data['barcode_image']}' style='max-width: 100%; max-height: 100%;' />
						</div>
					"""
				
				label_html += "</div>"
			
			html += label_html
			
		html += "</div>"
		
		# Simple breakdown handling for rendering, but CSS flex gap handles it visually.
		# For print formats, page breaks might be needed.
		
		self.preview_html = html
