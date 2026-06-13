# Copyright (c) 2024, DressUp and contributors
# For license information, please see license.txt

import frappe  # type: ignore
from frappe.model.document import Document  # type: ignore
from frappe.utils import flt, now  # type: ignore
from frappe.model.mapper import get_mapped_doc  # type: ignore


class CostEstimation(Document):
	def validate(self):
		"""Validate and calculate all totals"""
		self.validate_template_items()
		self.calculate_total_fabric()
		self.calculate_total_accessories()
		self.calculate_total_tailoring()
		self.calculate_total_finishing()
		self.calculate_suggested_selling_prices()

	def validate_template_items(self):
		"""Ensure no template items are added in materials or accessories child tables"""
		for row in self.materials:
			if row.item_code and frappe.db.get_value("Item", row.item_code, "has_variants"):
				frappe.throw(
					frappe._("Item {0} in Materials is a template item and cannot be added. Please select a specific variant.").format(row.item_code)
				)

		for row in self.accessories:
			if row.itemcode and frappe.db.get_value("Item", row.itemcode, "has_variants"):
				frappe.throw(
					frappe._("Item {0} in Accessories is a template item and cannot be added. Please select a specific variant.").format(row.itemcode)
				)


	def calculate_total_fabric(self):
		"""Calculate total fabric cost from materials table"""
		total = 0
		for row in self.materials:
			row.amount = flt(row.qty) * flt(row.rate)
			total += flt(row.amount)
		self.total_fabric = total
	
	def calculate_total_accessories(self):
		"""Calculate total accessories cost from accessories table"""
		total = 0
		for row in self.accessories:
			row.amount = flt(row.qty) * flt(row.rate)
			total += flt(row.amount)
		self.total_trim_and_accessories = total
	
	def calculate_total_tailoring(self):
		"""Calculate total tailoring/workstation charges"""
		total = (
			flt(self.cutting_f) +
			flt(self.sewing_f) +
			flt(self.machine_embroidery_f) +
			flt(self.hand_embroidery_f) +
			flt(self.hand_work_estimation) +
			flt(self.karchupi_f) +
			flt(self.screen_print_f) +
			flt(self.block_print_f) +
			flt(self.tie_dye)
		)
		self.total_tailoring = total
	
	def calculate_total_finishing(self):
		"""Calculate total finishing costs"""
		total = (
			flt(self.wash_iron) +
			flt(self.qc_packaging) +
			flt(self.transportation) +
			flt(self.fusingandpasting) +
			flt(self.others)
		)
		self.total_finishing = total
	
	def calculate_suggested_selling_prices(self):
		"""Calculate suggested selling prices based on different margin scenarios"""
		# Total cost = Fabric + Accessories + Tailoring + Finishing
		total_cost = (
			flt(self.total_fabric) +
			flt(self.total_trim_and_accessories) +
			flt(self.total_tailoring) +
			flt(self.total_finishing)
		)
		
		# Direct calculation using dynamic percentage fields
		
		# Screen Print/Machine Embroidery markup calculation
		if flt(self.screen_print_machine_emb_65):
			self.screen_print_machine_emb_only = total_cost * (1 + flt(self.screen_print_machine_emb_65) / 100)
		else:
			self.screen_print_machine_emb_only = 0
		
		# Pattern Variation markup calculation
		if flt(self.pattern_variation):
			self.for_pattern_variation_only = total_cost * (1 + flt(self.pattern_variation) / 100)
		else:
			self.for_pattern_variation_only = 0
			
		# Hand Embroidery markup calculation
		if flt(self.hand_embroidery_75):
			self.hand_embroidery_only = total_cost * (1 + flt(self.hand_embroidery_75) / 100)
		else:
			self.hand_embroidery_only = 0
	
	def on_update(self):
		"""Auto create/cancel stock reservation on save based on reserve_stock checkbox"""
		if self.reserve_stock:
			# Cancel existing reservations first (to handle item changes)
			self._cancel_existing_reservations()
			# Create fresh reservations
			self.create_stock_reservation_entries()
			frappe.msgprint("Stock Reservation Entries created successfully.", indicator="green", alert=True)
		else:
			# If reserve_stock is unchecked, cancel any existing reservations
			if self._has_existing_reservations():
				self._cancel_existing_reservations()
				frappe.msgprint("Stock Reservation Entries cancelled.", indicator="orange", alert=True)

	def before_submit(self):
		"""Validation before submission"""
		if not self.materials and not self.accessories:
			frappe.throw("Please add at least one material or accessory item before submitting")
		
		if flt(self.total_fabric) == 0 and flt(self.total_trim_and_accessories) == 0:
			frappe.throw("Total cost cannot be zero")

	def on_submit(self):
		"""Ensure stock reservation on submit if checked and not already reserved"""
		if self.reserve_stock and not self._has_existing_reservations():
			self.create_stock_reservation_entries()

	def on_cancel(self):
		self.cancel_stock_reservation_entries()

	def _has_existing_reservations(self):
		"""Check if any active Stock Reservation Entries exist for this document"""
		return frappe.db.exists("Stock Reservation Entry", {
			"voucher_type": self.doctype,
			"voucher_no": self.name,
			"docstatus": ["<", 2]
		})

	def _cancel_existing_reservations(self):
		"""Cancel and delete all associated Stock Reservation Entries, reset child table qty"""
		entries = frappe.get_all("Stock Reservation Entry", filters={
			"voucher_type": self.doctype,
			"voucher_no": self.name,
			"docstatus": ["<", 2]
		})

		for entry in entries:
			sre = frappe.get_doc("Stock Reservation Entry", entry.name)
			if sre.docstatus == 1:
				sre.cancel()
			frappe.delete_doc("Stock Reservation Entry", entry.name)

		self.db_set("stock_reservation_status", "Unreserved")

		# Reset reserved_qty in child tables
		for item in self.materials:
			item.db_set("reserved_qty", 0)
		for item in self.accessories:
			item.db_set("reserved_qty", 0)

	def create_stock_reservation_entries(self):
		"""Create Stock Reservation Entry for each item in materials and accessories"""
		has_reservation = False
		
		# Process Materials
		for item in self.materials:
			if item.item_code and item.warehouse and flt(item.qty) > 0:
				self.create_reservation_entry(item.item_code, item.warehouse, item.qty, item)
				has_reservation = True
		
		# Process Accessories
		for item in self.accessories:
			if item.itemcode and item.warehouse and flt(item.qty) > 0:
				self.create_reservation_entry(item.itemcode, item.warehouse, item.qty, item)
				has_reservation = True

		if has_reservation:
			self.db_set("stock_reservation_status", "Reserved")
		
	def create_reservation_entry(self, item_code, warehouse, qty, row):
		"""Helper to create a single Stock Reservation Entry"""
		from erpnext.stock.doctype.stock_reservation_entry.stock_reservation_entry import get_available_qty_to_reserve  # type: ignore
		
		available_qty = get_available_qty_to_reserve(item_code, warehouse)

		sre = frappe.get_doc({
			"doctype": "Stock Reservation Entry",
			"item_code": item_code,
			"warehouse": warehouse,
			"voucher_type": self.doctype,
			"voucher_no": self.name,
			"voucher_detail_no": row.name,
			"reserved_qty": qty,
			"voucher_qty": qty,
			"available_qty": available_qty,
			"company": self.company,
			"status": "Reserved"
		})
		sre.insert(ignore_permissions=True)
		sre.submit()
		row.db_set("reserved_qty", qty)

	def cancel_stock_reservation_entries(self):
		"""Cancel and delete all associated Stock Reservation Entries"""
		self._cancel_existing_reservations()


@frappe.whitelist()
def make_pre_production_sample(source_name, target_doc=None):
	"""Create Pre Production Sample from Cost Estimation"""
	
	def set_missing_values(source, target):
		target.start_time_date = now()
		target.read_confirm_carefully = "I confirm that all measurements, materials, and specifications have been reviewed and are accurate."
		
		# Get default Quality Inspection Template from Dressup Settings
		default_inspection = frappe.db.get_single_value("Dressup Settings", "default_pps_inspection")
		if default_inspection:
			target.link_nsnp = default_inspection
		else:
			frappe.throw("Please set the Default PPS Inspection in DressUp Settings.")
		
		# Add default size chart rows
		for size in ['36', '38', '40', '42', '44','46']:
			target.append('size_chart_in_inch', {'size_chart_in_inch': size})
	
	def update_fabric_item(source, target, source_parent):
		target.quantity = source.qty
		target.default_unit_of_measurement = source.uom
	
	def update_accessory_item(source, target, source_parent):
		target.item_code = source.itemcode
		target.quantity = source.qty
	
	doclist = get_mapped_doc(
		"Cost Estimation",
		source_name,
		{
			"Cost Estimation": {
				"doctype": "Pre Production Sample",
				"field_map": {
					"name": "cost_estimation",
					"category": "category",
					"item_name": "item_name",
					"designer": "designer",
					"designer_name": "designer_name",
					"design_no": "style_no",
					"cut_fit_style": "cut_fit_style",
					"collar_neck_style": "collar_neck_style",
					"side_cut": "side_cut",
					"session": "session",
					"sewing_finish": "sewing_finish",
					"source_warehouse": "source_warehouse",
					# Workstation Charges
					"cutting": "cutting",
					"fusing_bundling": "fusing_bundling",
					"sewing": "sewing",
					"machine_embroidery": "machine_embroidery",
					"hand_embroidery": "hand_embroidery",
					"hand_work": "hand_work",
					"screen_print": "screen_print",
					"block_print": "block_print",
					"tiedye": "tiedye",
					"karchupi": "karchupi",
					# Total Finishing
					"wash_iron": "wash_iron",
					"qc_packaging": "qc_packaging",
					"transportation": "transportation",
					"fusingandpasting": "fusingandpasting",
					"others": "others",
					"total_finishing": "total_finishing",
					# Workstation Charges Estimation
					"cutting_f": "cutting_f",
					"sewing_f": "sewing_f",
					"hand_work_estimation": "hand_work_estimation",
					"machine_embroidery_f": "machine_embroidery_f",
					"hand_embroidery_f": "hand_embroidery_f",
					"karchupi_f": "karchupi_f",
					"screen_print_f": "screen_print_f",
					"block_print_f": "block_print_f",
					"tie_dye": "tie_dye",
					"total_tailoring": "total_tailoring",
					# Margin & Suggested Selling Price
					"pattern_variation": "pattern_variation",
					"screen_print_machine_emb_65": "screen_print_machine_emb_65",
					"hand_embroidery_75": "hand_embroidery_75",
					"for_pattern_variation_only": "for_pattern_variation_only",
					"screen_print_machine_emb_only": "screen_print_machine_emb_only",
					"hand_embroidery_only": "hand_embroidery_only"
				},
				"field_no_map": ["naming_series"],
				"validation": {"docstatus": ["=", 1]}
			},
			"Cost Estimation Material": {
				"doctype": "PPS Fabric Item",
				"field_map": {
					"item_name": "item_name"
				},
				"postprocess": update_fabric_item
			},
			"Cost Estimation Accessory": {
				"doctype": "PPS Trim Accessories Item",
				"field_map": {
					"item_name": "item_name"
				},
				"postprocess": update_accessory_item
			}
		},
		target_doc,
		set_missing_values,
		ignore_permissions=True
	)
	
	return doclist

@frappe.whitelist()
def make_item(source_name, target_doc=None):
	from frappe.model.mapper import get_mapped_doc  # type: ignore

	item = get_mapped_doc(
		"Cost Estimation",
		source_name,
		{
			"Cost Estimation": {
				"doctype": "Item",
				"field_map": {
					"item_name": "item_name",
					"tech_pack_no": "item_code",
					"category": "item_group",
					"session": "session"
				}
			}
		},
		target_doc
	)
	return item


@frappe.whitelist()
def trigger_request_for_approval(docname):
	doc = frappe.get_doc("Cost Estimation", docname)
	notification = frappe.get_doc("Notification", "Cost Estamitation Approval")
	notification.send(doc)
	return True


@frappe.whitelist()
def update_stock_reservation(docname, reserve_stock):
	from frappe.utils import cint
	reserve_stock = cint(reserve_stock)
	
	doc = frappe.get_doc("Cost Estimation", docname)
	
	if doc.docstatus != 1:
		frappe.throw("Stock reservation can only be updated for submitted documents.")
	
	# Update the parent checkbox value in DB
	doc.db_set("reserve_stock", reserve_stock)
	doc.reserve_stock = reserve_stock
	
	if reserve_stock:
		# Cancel existing first (to avoid duplicates or handle updates)
		doc._cancel_existing_reservations()
		# Create fresh reservation entries
		doc.create_stock_reservation_entries()
		frappe.msgprint("Stock Reservation Entries updated successfully.", indicator="green", alert=True)
	else:
		doc._cancel_existing_reservations()
		frappe.msgprint("Stock Reservation Entries cancelled.", indicator="orange", alert=True)
		
	return True


@frappe.whitelist()
def create_stock_reservation_entries_via_dialog(docname, items_details):
	import json
	if isinstance(items_details, str):
		items_details = json.loads(items_details)
		
	doc = frappe.get_doc("Cost Estimation", docname)
	
	if doc.docstatus != 1:
		frappe.throw("Stock reservation can only be updated for submitted documents.")
		
	from erpnext.stock.doctype.stock_reservation_entry.stock_reservation_entry import get_available_qty_to_reserve
	
	created_any = False
	for item in items_details:
		row_id = item.get("row_id")
		child_doctype = item.get("child_doctype")
		item_code = item.get("item_code")
		warehouse = item.get("warehouse")
		qty_to_reserve = flt(item.get("qty_to_reserve"))
		
		if qty_to_reserve <= 0:
			continue
			
		available_qty = get_available_qty_to_reserve(item_code, warehouse)
		
		# Create Stock Reservation Entry
		sre = frappe.get_doc({
			"doctype": "Stock Reservation Entry",
			"item_code": item_code,
			"warehouse": warehouse,
			"voucher_type": doc.doctype,
			"voucher_no": doc.name,
			"voucher_detail_no": row_id,
			"reserved_qty": qty_to_reserve,
			"voucher_qty": qty_to_reserve,
			"available_qty": available_qty,
			"company": doc.company,
			"status": "Reserved"
		})
		sre.insert(ignore_permissions=True)
		sre.submit()
		
		# Update the specific child table row
		frappe.db.set_value(child_doctype, row_id, "reserved_qty", qty_to_reserve)
		created_any = True
		
	if created_any:
		# Reload the doc to get latest child table values
		doc.reload()
		
		# Recalculate status
		has_reservation = False
		all_reserved = True
		
		for row in doc.materials:
			if flt(row.reserved_qty) > 0:
				has_reservation = True
				if flt(row.reserved_qty) < flt(row.qty):
					all_reserved = False
			else:
				all_reserved = False
				
		for row in doc.accessories:
			if flt(row.reserved_qty) > 0:
				has_reservation = True
				if flt(row.reserved_qty) < flt(row.qty):
					all_reserved = False
			else:
				all_reserved = False
				
		if has_reservation:
			if all_reserved:
				doc.db_set("stock_reservation_status", "Reserved")
			else:
				doc.db_set("stock_reservation_status", "Partially Reserved")
			doc.db_set("reserve_stock", 1)
		else:
			doc.db_set("stock_reservation_status", "Unreserved")
			doc.db_set("reserve_stock", 0)
			
		frappe.msgprint("Stock Reservation Entries Created", alert=True, indicator="green")
		
	return True


@frappe.whitelist()
def cancel_stock_reservation_entries_via_dialog(docname, sre_list):
	import json
	if isinstance(sre_list, str):
		sre_list = json.loads(sre_list)
		
	doc = frappe.get_doc("Cost Estimation", docname)
	
	if doc.docstatus != 1:
		frappe.throw("Stock reservation can only be updated for submitted documents.")
		
	for sre_name in sre_list:
		sre = frappe.get_doc("Stock Reservation Entry", sre_name)
		if sre.docstatus == 1:
			sre.cancel()
			
		# Find the matching row in materials or accessories and reset/reduce its reserved_qty
		row_found = False
		for row in doc.materials:
			if row.name == sre.voucher_detail_no:
				new_reserved = max(0.0, flt(row.reserved_qty) - flt(sre.reserved_qty))
				row.db_set("reserved_qty", new_reserved)
				row_found = True
				break
		if not row_found:
			for row in doc.accessories:
				if row.name == sre.voucher_detail_no:
					new_reserved = max(0.0, flt(row.reserved_qty) - flt(sre.reserved_qty))
					row.db_set("reserved_qty", new_reserved)
					row_found = True
					break
					
		frappe.delete_doc("Stock Reservation Entry", sre_name)
		
	# Recalculate status
	has_reservation = False
	all_reserved = True
	
	doc.reload()
	for row in doc.materials:
		if flt(row.reserved_qty) > 0:
			has_reservation = True
			if flt(row.reserved_qty) < flt(row.qty):
				all_reserved = False
		else:
			all_reserved = False
			
	for row in doc.accessories:
		if flt(row.reserved_qty) > 0:
			has_reservation = True
			if flt(row.reserved_qty) < flt(row.qty):
				all_reserved = False
		else:
			all_reserved = False
			
	if has_reservation:
		if all_reserved:
			doc.db_set("stock_reservation_status", "Reserved")
		else:
			doc.db_set("stock_reservation_status", "Partially Reserved")
		doc.db_set("reserve_stock", 1)
	else:
		doc.db_set("stock_reservation_status", "Unreserved")
		doc.db_set("reserve_stock", 0)
			
	frappe.msgprint("Stock Reservation Entries Cancelled", alert=True, indicator="red")
	return True


@frappe.whitelist()
def update_submitted_items(docname, materials=None, accessories=None):
	import json
	if isinstance(materials, str):
		materials = json.loads(materials)
	if isinstance(accessories, str):
		accessories = json.loads(accessories)
		
	doc = frappe.get_doc("Cost Estimation", docname)
	if doc.docstatus != 1:
		frappe.throw("Items can only be updated for submitted documents.")
		
	# 1. Cancel existing stock reservations first
	doc._cancel_existing_reservations()
	
	# 2. Update child table materials
	if materials:
		for item in materials:
			row_name = item.get("docname")
			qty = flt(item.get("qty"))
			rate = flt(item.get("rate"))
			warehouse = item.get("warehouse")
			amount = qty * rate
			
			frappe.db.set_value("Cost Estimation Material", row_name, {
				"qty": qty,
				"rate": rate,
				"warehouse": warehouse,
				"amount": amount
			})
			
	# 3. Update child table accessories
	if accessories:
		for item in accessories:
			row_name = item.get("docname")
			qty = flt(item.get("qty"))
			rate = flt(item.get("rate"))
			warehouse = item.get("warehouse")
			amount = qty * rate
			
			frappe.db.set_value("Cost Estimation Accessory", row_name, {
				"qty": qty,
				"rate": rate,
				"warehouse": warehouse,
				"amount": amount
			})
			
	# 4. Reload doc to get updated child table rows
	doc.reload()
	
	# 5. Run calculations
	doc.calculate_total_fabric()
	doc.calculate_total_accessories()
	doc.calculate_total_tailoring()
	doc.calculate_total_finishing()
	doc.calculate_suggested_selling_prices()
	
	# 6. Update parent totals and suggested prices in database
	doc.db_set({
		"total_fabric": doc.total_fabric,
		"total_trim_and_accessories": doc.total_trim_and_accessories,
		"total_tailoring": doc.total_tailoring,
		"total_finishing": doc.total_finishing,
		"screen_print_machine_emb_only": doc.screen_print_machine_emb_only,
		"for_pattern_variation_only": doc.for_pattern_variation_only,
		"hand_embroidery_only": doc.hand_embroidery_only,
		"stock_reservation_status": "Unreserved",
		"reserve_stock": 0
	})
	
	frappe.msgprint("Items updated successfully.", indicator="green", alert=True)
	return True

