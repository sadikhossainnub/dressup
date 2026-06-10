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
		self.calculate_total_fabrics()
		self.calculate_total_trim_accessories()
		self.calculate_total_tailoring()
		self.calculate_total_finishing()
		self.calculate_total_production_qty()
		self.calculate_suggested_selling_prices()

	def calculate_total_fabrics(self):
		"""Calculate total amount of all fabrics"""
		from frappe.utils import flt
		self.total_fabrics = sum(flt(row.amount) for row in (self.fabrics or []))

	def calculate_total_trim_accessories(self):
		"""Calculate total amount of all trim & accessories"""
		from frappe.utils import flt
		self.total_trim_accessories = sum(flt(row.amount) for row in (self.trim_accessories or []))

	def calculate_total_production_qty(self):
		"""Calculate total production qty from size chart"""
		from frappe.utils import cint
		self.total_production_qty = sum(cint(row.production_qty) for row in (self.size_chart_in_inch or []))

	def calculate_total_tailoring(self):
		"""Calculate total tailoring/workstation charges"""
		from frappe.utils import flt
		self.total_tailoring = (
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

	def calculate_total_finishing(self):
		"""Calculate total finishing costs"""
		from frappe.utils import flt
		self.total_finishing = (
			flt(self.wash_iron) +
			flt(self.qc_packaging) +
			flt(self.transportation) +
			flt(self.fusingandpasting) +
			flt(self.others)
		)
	

	def calculate_suggested_selling_prices(self):
		"""Calculate suggested selling prices based on different margin scenarios"""
		from frappe.utils import flt
		# Total cost = Fabrics + Trim Accessories + Tailoring + Finishing
		total_cost = (
			flt(self.total_fabrics) +
			flt(self.total_trim_accessories) +
			flt(self.total_tailoring) +
			flt(self.total_finishing)
		)
		
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
		"""Create Stock Entry for material issue (Disabled)"""
		# Automatic Stock Entry creation disabled as per request
		pass

	def on_cancel(self):
		"""Cancel associated Stock Entry (Disabled)"""
		# Automatic Stock Entry cancellation disabled as per request
		pass


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


def link_stock_entry_to_pps(doc, method=None):
	"""Link Stock Entry to PPS if it's created from a Work Order which is linked to a PPS"""
	if not doc.work_order:
		return

	# Try finding PPS name from Work Order first
	pps_name = frappe.db.get_value("Work Order", doc.work_order, "pre_production_sample")

	# If not found (or column doesn't exist), try finding it by querying Pre Production Sample
	if not pps_name:
		pps_name = frappe.db.get_value("Pre Production Sample", {"work_order": doc.work_order}, "name")

	if pps_name:
		frappe.db.set_value("Pre Production Sample", pps_name, "stock_entry", doc.name)


def unlink_stock_entry_from_pps(doc, method=None):
	"""Unlink Stock Entry from PPS if it's cancelled or deleted"""
	# Find PPS that is linked to this Stock Entry
	pps_name = frappe.db.get_value("Pre Production Sample", {"stock_entry": doc.name}, "name")
	if pps_name:
		frappe.db.set_value("Pre Production Sample", pps_name, "stock_entry", None)


@frappe.whitelist()
def update_submitted_size_chart(docname, size_chart):
	import json
	from frappe.utils import cint

	if isinstance(size_chart, str):
		size_chart = json.loads(size_chart)

	# Check authorization: Only Manufacturing Manager is allowed
	if not "Manufacturing Manager" in frappe.get_roles(frappe.session.user):
		frappe.throw(_("Not authorized. Only users with the 'Manufacturing Manager' role can update the size chart of a submitted Pre Production Sample."))

	doc = frappe.get_doc("Pre Production Sample", docname)
	if doc.docstatus != 1:
		frappe.throw(_("Size Chart can only be updated for submitted documents."))

	# Delete existing child rows
	frappe.db.delete("Size Chart in Inch", {"parent": docname})

	total_qty = 0
	# Insert new child rows
	for idx, row in enumerate(size_chart):
		child = frappe.get_doc({
			"doctype": "Size Chart in Inch",
			"parent": docname,
			"parenttype": "Pre Production Sample",
			"parentfield": "size_chart_in_inch",
			"idx": idx + 1,
			"size_chart_in_inch": row.get("size_chart_in_inch"),
			"production_qty": cint(row.get("production_qty")),
			"color": row.get("color"),
			"length": row.get("length"),
			"neck": row.get("neck"),
			"waist": row.get("waist"),
			"sleeve": row.get("sleeve"),
			"sleeve_opening": row.get("sleeve_opening"),
			"bottom_length": row.get("bottom_length"),
			"bottom_waist": row.get("bottom_waist"),
			"bottom_thigh": row.get("bottom_thigh"),
			"bottom_crotch": row.get("bottom_crotch"),
			"leg_opening": row.get("leg_opening"),
			"shrug_koti_length": row.get("shrug_koti_length"),
			"koti_sleeve": row.get("koti_sleeve"),
			"koti_sleeve_opening": row.get("koti_sleeve_opening"),
			"others1": row.get("others1")
		})
		child.insert(ignore_permissions=True)
		total_qty += cint(row.get("production_qty"))

	# Update parent total production qty
	doc.db_set("total_production_qty", total_qty)

	# Commit changes
	frappe.db.commit()

	return True

