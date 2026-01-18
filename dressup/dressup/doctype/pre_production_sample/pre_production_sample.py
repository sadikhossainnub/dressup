# Copyright (c) 2024, DressUp and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import now
from frappe.model.mapper import get_mapped_doc


class PreProductionSample(Document):
	def onload(self):
		"""Add default size chart on new doc"""
		if self.is_new() and not self.size_chart_in_inch:
			for size in ['36', '38', '40', '42']:
				self.append('size_chart_in_inch', {'size_chart_in_inch': size})
	
	def validate(self):
		"""Auto-populate fields from Tech Pack"""
		if self.tech_pack_no and not self.is_new():
			self.fetch_tech_pack_data()
	
	def fetch_tech_pack_data(self):
		"""Fetch data from Sketch Specification Sample Making Sheet"""
		if not self.tech_pack_no:
			return
		
		try:
			tech_pack = frappe.get_doc("Sketch Specification Sample Making Sheet", self.tech_pack_no)
			
			# Auto-populate Quality Inspection Template if not set
			if not self.link_nsnp:
				quality_templates = frappe.get_all("Quality Inspection Template", limit=1)
				if quality_templates:
					self.link_nsnp = quality_templates[0].name
			
			# Auto-populate disclaimer text
			if not self.read_confirm_carefully:
				self.read_confirm_carefully = "I confirm that all measurements, materials, and specifications have been reviewed and are accurate."
			
			# Set start time if not set
			if not self.start_time_date:
				self.start_time_date = now()
				
		except Exception as e:
			frappe.log_error(f"Error fetching tech pack data: {str(e)}", "PPS Auto-populate Error")
	
	def before_submit(self):
		"""Validation before submission"""
		if not self.fabrics and not self.trim_accessories and not self.fabric_dupatta:
			frappe.throw("Please add at least one fabric, trim/accessory, or dupatta item")
		
		if not self.size_chart_in_inch:
			frappe.throw("Size chart is required")
		
		# User requested mandatory fields for submission
		if not self.pattern_master_note:
			frappe.throw("Pattern Master Note is mandatory for submission")
		if not self.pps_front:
			frappe.throw("PPS Front image is mandatory for submission")
		if not self.pps_back:
			frappe.throw("PPS Back image is mandatory for submission")
		
		# Check if Quality Inspection exists and is submitted
		qi = frappe.db.exists("Quality Inspection", {
			"reference_type": "Pre Production Sample",
			"reference_name": self.name,
			"docstatus": 1
		})
		if not qi:
			frappe.throw("Please create and submit Quality Inspection before submitting PPS")
		
		# Auto-set finish time
		if not self.finish_time_date:
			self.finish_time_date = now()


@frappe.whitelist()
def make_quality_inspection(source_name, target_doc=None):
	"""Create Quality Inspection from Pre Production Sample"""
	
	def set_missing_values(source, target):
		target.inspection_type = "In Process"
		target.reference_type = "Pre Production Sample"
		target.reference_name = source.name
		target.report_date = now()
		
		# Get readings from template
		if source.link_nsnp:
			target.quality_inspection_template = source.link_nsnp
			target.get_item_specification_details()
	
	doclist = get_mapped_doc(
		"Pre Production Sample",
		source_name,
		{
			"Pre Production Sample": {
				"doctype": "Quality Inspection",
				"field_map": {
					"name": "reference_name",
					"tech_pack_no": "item_code"
				},
				"validation": {"docstatus": ["=", 1]}
			}
		},
		target_doc,
		set_missing_values
	)
	
	return doclist