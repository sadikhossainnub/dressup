import frappe
from frappe.model.document import Document


class BarcodeLabelSetting(Document):
	def validate(self):
		if self.label_width <= 0:
			frappe.throw("Label width must be greater than 0")
		if self.label_height <= 0:
			frappe.throw("Label height must be greater than 0")