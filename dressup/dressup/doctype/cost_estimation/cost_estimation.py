# Copyright (c) 2024, DressUp and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt


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
		
		# Pattern Variation: 52% margin
		# If margin is 52%, then cost is 48% of selling price
		# Selling Price = Cost / 0.48
		if flt(self.pattern_variation):
			margin_percent = flt(self.pattern_variation) / 100
			self.for_pattern_variation_only = total_cost / (1 - margin_percent) if margin_percent < 1 else 0
		else:
			# Default 52% margin
			self.for_pattern_variation_only = total_cost / 0.48
		
		# Screen Print/Machine Embroidery: 65% margin
		# Selling Price = Cost / 0.35
		self.screen_print_machine_emb_only = total_cost / 0.35
		
		# Hand Embroidery: 75% margin
		# Selling Price = Cost / 0.25
		self.hand_embroidery_only = total_cost / 0.25
	
	def before_submit(self):
		"""Validation before submission"""
		if not self.materials and not self.accessories:
			frappe.throw("Please add at least one material or accessory item before submitting")
		
		if flt(self.total_fabric) == 0 and flt(self.total_trim_and_accessories) == 0:
			frappe.throw("Total cost cannot be zero")