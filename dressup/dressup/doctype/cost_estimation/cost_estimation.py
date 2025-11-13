# Copyright (c) 2024, DressUp and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class CostEstimation(Document):
	def validate(self):
		self.calculate_totals()
	
	def calculate_totals(self):
		# Calculate total fabric
		total_fabric = 0
		if self.materials:
			for item in self.materials:
				if item.amount:
					total_fabric += item.amount
		self.total_fabric = total_fabric
		
		# Calculate total tailoring
		cutting = self.cutting or 0
		sewing = self.sewing or 0
		self.total_tailoring = cutting + sewing
		
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