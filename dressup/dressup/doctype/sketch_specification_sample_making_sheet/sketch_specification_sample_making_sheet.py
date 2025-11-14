# Copyright (c) 2024, DressUp and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class SketchSpecificationSampleMakingSheet(Document):
	def before_insert(self):
		if not self.designer:
			employee = frappe.db.get_value("Employee", {"user_id": frappe.session.user}, "name")
			if employee:
				self.designer = employee