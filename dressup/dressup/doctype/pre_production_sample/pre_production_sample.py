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
			for size in ['36', '38', '40', '42','44']:
				self.append('size_chart_in_inch', {'size_chart_in_inch': size})
	
	def after_insert(self):
		"""When PPS is created from CE, release stock reservation"""
		if self.cost_estimation:
			self.release_stock_reservation()

	def release_stock_reservation(self):
		"""Cancel stock reservation entries from parent Cost Estimation"""
		ce = frappe.get_doc("Cost Estimation", self.cost_estimation)
		ce.cancel_stock_reservation_entries()
		frappe.msgprint(
			f"Stock reservation from {self.cost_estimation} has been released",
			indicator="green", alert=True
		)
	
	def validate(self):
		"""Auto-populate fields from Tech Pack"""
		if self.tech_pack_no:
			self.fetch_tech_pack_data()
	
	def fetch_tech_pack_data(self):
		"""Fetch data from Sketch Specification"""
		if not self.tech_pack_no:
			return
		
		try:
			tech_pack = frappe.get_doc("Sketch Specification", self.tech_pack_no)
			
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
		qi = frappe.db.get_value("Quality Inspection", {
			"reference_type": "Pre Production Sample",
			"reference_name": self.name,
			"docstatus": 1
		}, ["name", "status"], as_dict=True)
		if not qi:
			frappe.throw("Please create and submit Quality Inspection before submitting PPS")
		if qi.status != "Accepted":
			frappe.throw(f"Quality Inspection must be Accepted before submitting PPS. Current status: {qi.status}")
		
		# Auto-set finish time
		if not self.finish_time_date:
			self.finish_time_date = now()

	def on_submit(self):
		"""Create Stock Entry for material issue"""
		if not self.source_warehouse:
			frappe.throw("Source Warehouse is required for stock reduction")
		company = frappe.defaults.get_defaults().company
		if not company:
			frappe.throw("Default Company is not configured. Please set a default company before submitting PPS")

		expense_account = frappe.db.get_value("Company", company, "default_expense_account")
		if not expense_account:
			frappe.throw(
				f"Default Expense Account is not set for company {company}. "
				"Please configure Company.default_expense_account"
			)
		
		# Collect all items with actual quantity > 0
		items = []
		for table in ['fabrics', 'trim_accessories', 'fabric_dupatta']:
			# Check if table exists and is not None
			table_data = self.get(table)
			if table_data:
				for row in table_data:
					if row.actual_quantity:
						items.append({
							"item_code": row.item_code,
							"qty": row.actual_quantity,
							"uom": row.default_unit_of_measurement,
							"s_warehouse": self.source_warehouse,
							"t_warehouse": None,
							"expense_account": expense_account,
						})
		
		if not items:
			return

		# Create Stock Entry
		stock_entry = frappe.get_doc({
			"doctype": "Stock Entry",
			"stock_entry_type": "Material Issue",
			"company": company,
			"items": items,
			"remarks": f"Issued for Pre Production Sample: {self.name}"
		})
		stock_entry.insert()
		stock_entry.submit()
		
		self.db_set("stock_entry", stock_entry.name)

	def on_cancel(self):
		"""Cancel associated Stock Entry"""
		if self.stock_entry:
			se = frappe.get_doc("Stock Entry", self.stock_entry)
			if se.docstatus == 1:
				se.cancel()
			self.db_set("stock_entry", None)


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
					"item_code": "item_code"
				}
			}
		},
		target_doc,
		set_missing_values
	)
	
	return doclist

@frappe.whitelist()
def make_bom(source_name, bom_type="Sample Making"):
	"""Create BOM from PPS - Sample or Bulk"""
	from frappe.utils import flt
	
	pps = frappe.get_doc("Pre Production Sample", source_name)

	bom_items = []
	for table in ['fabrics', 'trim_accessories', 'fabric_dupatta']:
		for row in (pps.get(table) or []):
			if row.item_code:
				qty = flt(row.actual_quantity) or flt(row.quantity)
				if qty > 0:
					bom_items.append({
						"item_code": row.item_code,
						"qty": qty,
						"uom": row.default_unit_of_measurement,
						"rate": flt(row.rate)
					})

	bom_data = {
		"doctype": "BOM",
		"item": pps.item_code,
		"quantity": 1,
		"company": frappe.defaults.get_defaults().company,
		"items": bom_items,
		"is_default": 1 if bom_type == "Bulk Production" else 0
	}

	# Use only legacy fieldnames (no custom_ prefix).
	if frappe.db.has_column("BOM", "pre_production_sample"):
		bom_data["pre_production_sample"] = pps.name

	if frappe.db.has_column("BOM", "tech_pack_no"):
		bom_data["tech_pack_no"] = pps.tech_pack_no

	if frappe.db.has_column("BOM", "custom_bom_type"):
		bom_data["custom_bom_type"] = bom_type
	if frappe.db.has_column("BOM", "bom_type"):
		bom_data["bom_type"] = bom_type

	bom = frappe.get_doc(bom_data)
	bom.insert()

	# Link back to PPS
	if bom_type == "Sample Making":
		pps.db_set("sample_bom", bom.name)
	else:
		pps.db_set("production_bom", bom.name)

	return bom.name

def link_work_order_to_pps(doc, method):
	"""Auto-link Work Order to PPS when created from BOM"""
	if not doc.bom_no:
		return

	fields = []
	bom_pps_field = None
	if frappe.db.has_column("BOM", "pre_production_sample"):
		bom_pps_field = "pre_production_sample"
		fields.append("pre_production_sample")

	bom_tech_pack_field = None
	if frappe.db.has_column("BOM", "tech_pack_no"):
		bom_tech_pack_field = "tech_pack_no"
		fields.append("tech_pack_no")

	if not fields:
		return

	bom_data = frappe.db.get_value("BOM", doc.bom_no, fields, as_dict=True)
	if not bom_data:
		return

	# 1) Carry tech pack from BOM -> Work Order
	tech_pack_no = bom_data.get("tech_pack_no")
	if tech_pack_no:
		if frappe.db.has_column("Work Order", "tech_pack_no"):
			doc.db_set("tech_pack_no", tech_pack_no)

	# 2) Carry PPS link from BOM -> Work Order and update PPS.work_order
	pps_name = bom_data.get(bom_pps_field) if bom_pps_field else None
	if pps_name:
		if frappe.db.has_column("Work Order", "pre_production_sample"):
			doc.db_set("pre_production_sample", pps_name)

		frappe.db.set_value("Pre Production Sample", pps_name, "work_order", doc.name)
