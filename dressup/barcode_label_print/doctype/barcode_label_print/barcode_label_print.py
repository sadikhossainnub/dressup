# Copyright (c) 2024, Prime Technology of Bangladesh and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from dressup.dressup.barcode_label_print.utils import get_barcode_base64

class BarcodeLabelPrint(Document):
	def validate(self):
		self.generate_preview()

	def generate_preview(self):
		if not self.label_template:
			return

		template = frappe.get_doc("Barcode Label Template", self.label_template)
		
		# Determine what to encode in the barcode
		# Priority: Serial No > Batch No > Item Code
		code_value = self.item_code
		if self.batch_no:
			code_value = self.batch_no
		if self.serial_no:
			code_value = self.serial_no
			
		barcode_image = get_barcode_base64(template.barcode_type, code_value)
		
		# Prepare data for rendering
		data = {
			"item_code": self.item_code,
			"item_name": self.item_name,
			"garment_size": self.garment_size,
			"batch_no": self.batch_no,
			"serial_no": self.serial_no,
			"expiry_date": self.expiry_date,
			"company": frappe.defaults.get_user_default("Company"),
			"barcode_image": barcode_image,
			"template": template
		}
		
		# Render HTML
		# We'll construct a simple HTML here. For production, maybe use a Jinja template file.
		# But for preview, inline HTML is fine.
		
		html = f"""
		<div style="
			width: {template.label_width}mm;
			height: {template.label_height}mm;
			border: 1px solid #000;
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
		">
		"""
		
		if template.include_company_name and data.get("company"):
			html += f"<div style='font-weight: bold;'>{data['company']}</div>"
			
		if template.include_item_name and data.get("item_name"):
			html += f"<div>{data['item_name']}</div>"
			
		if template.include_item_code and data.get("item_code"):
			html += f"<div>{data['item_code']}</div>"
			
		if template.include_garment_size and data.get("garment_size"):
			html += f"<div>Size: {data['garment_size']}</div>"
			
		if barcode_image:
			html += f"<img src='{barcode_image}' style='max-width: 100%; max-height: 50%; margin: 2px 0;' />"
			
		if template.include_batch_no and data.get("batch_no"):
			html += f"<div>Batch: {data['batch_no']}</div>"
			
		if template.include_serial_no and data.get("serial_no"):
			html += f"<div>SN: {data['serial_no']}</div>"
			
		if template.include_expiry_date and data.get("expiry_date"):
			html += f"<div>Exp: {data['expiry_date']}</div>"
			
		html += "</div>"
		
		self.preview_html = html
