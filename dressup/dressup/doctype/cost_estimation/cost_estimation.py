# Copyright (c) 2024, DressUp and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class CostEstimation(Document):
	def validate(self):
		self._calculate_all_amounts()
		self.calculate_totals()
	
	def _calculate_all_amounts(self):
		"""Calculate amounts for all estimation tables"""
		table_configs = [
			('materials', 'qty', 'rate'),
			('accessories', 'qty', 'unit_price'),
			('cutting', 'quantity', 'rate'),
			('sewing', 'quantity', 'rate'),
			('hand_work_estimation', 'quantity', 'rate')
		]
		
		for table_name, qty_field, rate_field in table_configs:
			table = getattr(self, table_name, None)
			if table:
				for item in table:
					qty = getattr(item, qty_field, 0) or 0
					rate = getattr(item, rate_field, 0) or 0
					item.amount = qty * rate if qty and rate else 0
	
	def _calculate_table_total(self, table_name):
		"""Calculate total amount for a table"""
		table = getattr(self, table_name, None)
		return sum(item.amount or 0 for item in table) if table else 0
	
	def calculate_totals(self):
		# Calculate table totals
		self.total_fabric = self._calculate_table_total('materials')
		self.total_cutting = self._calculate_table_total('cutting')
		self.total_sewing = self._calculate_table_total('sewing')
		self.total_hand_work = self._calculate_table_total('hand_work_estimation')
		
		# Calculate total tailoring
		self.total_tailoring = self.total_cutting + self.total_sewing + self.total_hand_work
		
		# Calculate total finishing
		wash_iron = self.wash_iron or 0
		qc_packaging = self.qc_packaging or 0
		transportation = self.transportation or 0
		producer_profit = self.producer_profit or 0
		self.total_finishing = wash_iron + qc_packaging + transportation + producer_profit
		
		# Calculate overhead markup
		if self.overhead_markup_71:
			base_amount = total_fabric + self.total_tailoring + self.total_finishing
			self.overhead_markup_custom = base_amount * (self.overhead_markup_71 / 100)