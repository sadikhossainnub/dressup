# Copyright (c) 2024, DressUp and contributors
# For license information, please see license.txt

import frappe  # type: ignore
from frappe.model.document import Document  # type: ignore
from frappe.utils import flt, now  # type: ignore
from frappe.model.mapper import get_mapped_doc  # type: ignore


class CostEstimation(Document):
	def validate(self):
		"""Validate and calculate all totals"""
		self.calculate_total_fabric()
		self.calculate_total_accessories()
		self.calculate_total_tailoring()
		self.calculate_total_finishing()
		self.calculate_suggested_selling_prices()
	
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
			flt(self.transportation)
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
	
	def before_submit(self):
		"""Validation before submission"""
		if not self.materials and not self.accessories:
			frappe.throw("Please add at least one material or accessory item before submitting")
		
		if flt(self.total_fabric) == 0 and flt(self.total_trim_and_accessories) == 0:
			frappe.throw("Total cost cannot be zero")


@frappe.whitelist()
def make_pre_production_sample(source_name, target_doc=None):
	"""Create Pre Production Sample from Cost Estimation"""
	
	def set_missing_values(source, target):
		target.start_time_date = now()
		target.read_confirm_carefully = "I confirm that all measurements, materials, and specifications have been reviewed and are accurate."
		
		# Get first Quality Inspection Template
		quality_templates = frappe.get_all("Quality Inspection Template", limit=1)
		if quality_templates:
			target.link_nsnp = quality_templates[0].name
		
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
					"category": "category",
					"item_name": "item_name",
					"cut_fit_style": "cut_fit_style",
					"collar_neck_style": "collar_neck_style",
					"side_cut": "side_cut",
					"seson": "seson",
					"sewing_finish": "sewing_finish"
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
		set_missing_values
	)
	
	return doclist