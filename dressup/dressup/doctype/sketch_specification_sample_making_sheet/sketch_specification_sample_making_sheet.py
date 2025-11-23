# Copyright (c) 2024, DressUp and contributors
# For license information, please see license.txt

import frappe  # type: ignore
from frappe.model.document import Document  # type: ignore
import random


class SketchSpecificationSampleMakingSheet(Document):
	def before_insert(self):
		if not self.designer:
			employee = frappe.get_value("Employee", {"user_id": frappe.session.user}, "name")
			if employee:
				self.designer = employee

	def on_submit(self):
		self.db_set("submission_date", frappe.utils.now_datetime())
		self.create_cost_estimation()

	def create_cost_estimation(self):
		from frappe.model.mapper import get_mapped_doc  # type: ignore

		def set_missing_values(source, target):
			pass

		cost_est = get_mapped_doc(
			"Sketch Specification Sample Making Sheet",
			self.name,
			{
				"Sketch Specification Sample Making Sheet": {
					"doctype": "Cost Estimation",
					"field_map": {
						"name": "tech_pack_no",
						"item_name": "item_name",
						"category": "category",
						"designer": "designer",
						"design_no": "design_no"
					}
				}
			},
			None,
			set_missing_values
		)
		cost_est.flags.ignore_validate = True
		cost_est.insert(ignore_mandatory=True)
		frappe.msgprint(f"Cost Estimation {cost_est.name} created successfully")

	def before_save(self):
		if self.designer:
			employee = frappe.get_doc("Employee", self.designer)
			abbr = employee.get("abbr") or ""
			random_num = random.randint(1000, 9999)
			self.design_no = f"{abbr}{random_num}"

@frappe.whitelist()
def make_cost_estimation(source_name, target_doc=None):
	from frappe.model.mapper import get_mapped_doc  # type: ignore

	cost_est = get_mapped_doc(
		"Sketch Specification Sample Making Sheet",
		source_name,
		{
			"Sketch Specification Sample Making Sheet": {
				"doctype": "Cost Estimation",
				"field_map": {
					"name": "tech_pack_no",
					"item_name": "item_name",
					"category": "category",
					"designer": "designer",
					"design_no": "design_no"
				}
			}
		},
		target_doc
	)
	return cost_est