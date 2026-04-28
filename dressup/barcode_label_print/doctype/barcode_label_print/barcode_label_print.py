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
			code_value = item.get("item_code")
			if item.get("batch_no"):
				code_value = item.get("batch_no")
			if item.get("serial_no"):
				code_value = item.get("serial_no")
				
			barcode_image = get_barcode_base64(template.barcode_type, code_value)
			
			qty = item.qty if item.qty > 0 else 1
			for _ in range(qty):
				items_data.append({
					"item_code": item.get("item_code"),
					"item_name": item.get("item_name"),
					"batch_no": item.get("batch_no"),
					"serial_no": item.get("serial_no"),
					"price": item.get("price"),
					"color": item.get("color"),
					"size": item.get("size"),
					"base": item.get("base"),
					"session": item.get("session"),
					"expiry_date": item.get("expiry_date"),
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
			padding-left: 0.5mm;
			padding-right: 1.5mm;
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
				
				# Fetch additional item details for preview
				item_doc = frappe.get_doc("Item", data.get("item_code")) if data.get("item_code") else None
				description_text = frappe.utils.strip_html_tags(item_doc.description or "") if item_doc else ""
				
				# Attributes
				color_val = data.get("color") or ""
				size_val = data.get("size") or ""
				base_val = data.get("base") or ""
				
				if item_doc and item_doc.attributes:
					for attr in item_doc.attributes:
						if not color_val and 'color' in attr.attribute.lower():
							color_val = attr.attribute_value
							
						if not size_val and 'size' in attr.attribute.lower():
							size_val = attr.attribute_value
							
				# Calculate sizes based on font_size
				base_fs = template.font_size or 10
				
				label_html = f"""

				<div style="
					width: {template.label_width}mm;
					height: {template.label_height}mm;
					box-sizing: border-box;
					padding: 1.5mm 1mm;
					font-family: Arial, sans-serif;
					background: white;
					page-break-inside: avoid;
					border: 1px solid #ccc;
					display: flex;
					flex-direction: column;
					justify-content: flex-start;
					align-items: stretch;
					overflow: hidden;
				">
				"""
				
				# 1. Item Code (Top Center)
				if data.get("item_code"):
					label_html += f"""
						<div style="
							text-align: center;
							font-size: {base_fs * 1.3}pt;
							font-weight: 500;
							line-height: 1.2;
							margin-bottom: 0.5mm;
							white-space: nowrap;
							overflow: hidden;
							text-overflow: ellipsis;
						">{data['item_code']}</div>
					"""
				
				# 2. Barcode
				if data.get("barcode_image"):
					label_html += f"""
						<div style="
							width: 95%;
							height: 3mm;
							margin: 0 auto;
							display: flex;
							justify-content: center;
							align-items: center;
							margin-bottom: 0.5mm;
						">
							<img src='{data['barcode_image']}' style='max-width: 100%; width: 100%; height: 100%; object-fit: contain; image-rendering: pixelated; image-rendering: crisp-edges;' />
						</div>
					"""
					
				# 3. Serial No (left) + Session (right)
				serial_display = data.get('serial_no') or data.get('batch_no') or ""
				session_val = data.get('session') or ""
				label_html += f"""
					<div style="
						width: 100%;
						display: flex;
						justify-content: space-between;
						align-items: baseline;
						font-size: {base_fs * 1.5}pt;
						font-weight: 500;
						margin-bottom: 0.5mm;
						padding: 0 0.5mm;
						line-height: 1;
					">
						<span style="text-align: left; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 70%;">{serial_display}</span>
						<span style="text-align: right; white-space: nowrap; font-weight: 600;">{session_val}</span>
					</div>
				"""
				
				# 4. Item Name + Description
				if description_text:
					label_html += f"""
						<div style="
							font-size: {base_fs * 0.9}pt;
							font-weight: 400;
							line-height: 1;
							width: 100%;
							max-height: 4mm;
							overflow: hidden;
							padding: 0 0.5mm;
							margin-bottom: 00mm;
							display: -webkit-box;
							-webkit-line-clamp: 2;
							-webkit-box-orient: vertical;
						">{description_text}</div>
					"""
					
				# 5. Attributes (Color + Size)
				label_html += f"""
					<div style="
						width: 100%;
						display: flex;
						justify-content: space-between;
						font-size: {base_fs}pt;
						font-weight: 400;
						margin-bottom: 0.5mm;
						padding: 0 0.5mm;
						line-height: 1.2;
					">
						<span>C: {color_val}</span>
						<span>S: {size_val}</span>
						<span>B: {base_val}</span>
					</div>
				"""
				
				# 6. Price
				if data.get("price"):
					price_val = frappe.format_value(data['price'], {'fieldtype': 'Currency'})
					label_html += f"""
						<div style="
							width: 100%;
							text-align: center;
							font-size: {base_fs * 1.1}pt;
							font-weight: 800;
							margin-top: auto;
							padding-bottom: 0.5mm;
							letter-spacing: 0.2mm;
						">BDT: {int(data['price'])} + VAT</div>
					"""
				
				label_html += "</div>"
			
			html += label_html
			
		html += "</div>"
		
		# Simple breakdown handling for rendering, but CSS flex gap handles it visually.
		# For print formats, page breaks might be needed.
		
		self.preview_html = html


@frappe.whitelist()
def get_items_by_group(item_group):
	"""Fetch all items from a given Item Group for bulk adding."""
	items = frappe.get_all(
		"Item",
		filters={"item_group": item_group, "disabled": 0},
		fields=["name as item_code", "item_name", "standard_rate"],
		order_by="item_name asc",
		limit_page_length=500
	)
	return items


@frappe.whitelist()
def get_serial_nos_for_item(item_code, warehouse=None):
	"""Fetch all active (in-stock) serial numbers for a given item.

	Args:
		item_code: The Item Code to look up serial numbers for.
		warehouse: Optional warehouse filter.

	Returns:
		List of dicts with serial_no and warehouse fields.
	"""
	filters = {
		"item_code": item_code,
		"status": "Active",
	}
	if warehouse:
		filters["warehouse"] = warehouse

	serial_nos = frappe.get_all(
		"Serial No",
		filters=filters,
		fields=["name as serial_no", "warehouse", "batch_no"],
		order_by="name asc",
		limit_page_length=0
	)
	return serial_nos


@frappe.whitelist()
def get_item_price(item_code, price_list=None):
	"""Fetch the best price for an item.

	Priority:
		1. Item Price from the specified Price List (Selling)
		2. Valuation Rate from the Item master

	Args:
		item_code: The Item Code to look up.
		price_list: Optional Price List name to fetch from.

	Returns:
		dict with price and source fields.
	"""
	price = 0
	source = "none"

	# Priority 1: Item Price from Price List
	if price_list:
		item_price = frappe.db.get_value(
			"Item Price",
			{
				"item_code": item_code,
				"price_list": price_list,
				"selling": 1,
			},
			"price_list_rate",
			order_by="valid_from desc",
		)
		if item_price:
			price = item_price
			source = "item_price"

	# Fallback: try any selling price list if no specific one given
	if not price and not price_list:
		item_price = frappe.db.get_value(
			"Item Price",
			{
				"item_code": item_code,
				"selling": 1,
			},
			"price_list_rate",
			order_by="valid_from desc",
		)
		if item_price:
			price = item_price
			source = "item_price"

	# Priority 2: Valuation Rate from Item
	if not price:
		valuation_rate = frappe.db.get_value("Item", item_code, "valuation_rate")
		if valuation_rate:
			price = valuation_rate
			source = "valuation_rate"

	# Final fallback: standard_rate
	if not price:
		standard_rate = frappe.db.get_value("Item", item_code, "standard_rate")
		if standard_rate:
			price = standard_rate
			source = "standard_rate"

	return {"price": price or 0, "source": source}

@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_item_attributes_query(doctype, txt, searchfield, start, page_len, filters):
	item_code = filters.get("item_code")
	if not item_code:
		return []

	# In Frappe, the child table for attributes in Item is 'Item Variant Attribute'
	# We fetch the attribute names for this specific item
	attributes = frappe.db.sql("""
		select attribute 
		from `tabItem Variant Attribute` 
		where parent = %s and parenttype = 'Item'
	""", (item_code,), as_dict=0)
	
	if not attributes:
		return []
		
	attr_names = [a[0] for a in attributes]
	
	query = """
		select name from `tabItem Attribute`
		where name in ({}) and name like %s
		order by name limit %s offset %s
	""".format(", ".join(["%s"] * len(attr_names)))
	
	args = attr_names + [f"%{txt}%", page_len, start]
	return frappe.db.sql(query, args)


@frappe.whitelist()
def get_item_attributes_data(item_code):
	if not item_code:
		return []
		
	return frappe.db.sql("""
		select attribute, attribute_value
		from `tabItem Variant Attribute`
		where parent = %s and parenttype = 'Item'
	""", (item_code,), as_dict=1)

