import frappe
from frappe import _
from erpnext.stock.doctype.quality_inspection.quality_inspection import QualityInspection


class CustomQualityInspection(QualityInspection):
	def validate(self):
		"""Override validate to allow Pre Production Sample as reference type"""
		# Temporarily store reference_type if it's Pre Production Sample
		original_reference_type = self.reference_type
		
		# If reference type is Pre Production Sample, temporarily change it to pass validation
		if self.reference_type == "Pre Production Sample":
			# Set to a valid type temporarily for parent validation
			self.reference_type = "Stock Entry"
		
		# Call parent validate
		super().validate()
		
		# Restore original reference type
		self.reference_type = original_reference_type
	
	def set_child_row_reference(self):
		"""Override to skip child row reference for Pre Production Sample"""
		# Skip child row reference logic for Pre Production Sample
		if self.reference_type == "Pre Production Sample":
			return
		
		# Call parent method for all other reference types
		super().set_child_row_reference()
	
	def update_qc_reference(self, remove_reference=False):
		"""Override to skip update for Pre Production Sample"""
		# Skip update logic for Pre Production Sample
		if self.reference_type == "Pre Production Sample":
			return
		
		# Call parent method for all other reference types
		super().update_qc_reference(remove_reference)
