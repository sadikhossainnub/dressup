# Copyright (c) 2026, Prime Technology of Bangladesh and contributors
// For license information, please see license.txt

import frappe
from frappe import _

def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	return columns, data

def get_columns():
	return [
		{
			"label": _("Work Order"),
			"fieldname": "work_order",
			"fieldtype": "Link",
			"options": "Work Order",
			"width": 120
		},
		{
			"label": _("BOM Variant"),
			"fieldname": "bom_variant",
			"fieldtype": "Data",
			"width": 130
		},
		{
			"label": _("Has Series"),
			"fieldname": "has_series",
			"fieldtype": "Data",
			"width": 100
		},
		{
			"label": _("Item Code"),
			"fieldname": "item_code",
			"fieldtype": "Link",
			"options": "Item",
			"width": 120
		},
		{
			"label": _("Item Name"),
			"fieldname": "item_name",
			"fieldtype": "Data",
			"width": 150
		},
		{
			"label": _("Source Warehouse"),
			"fieldname": "source_warehouse",
			"fieldtype": "Link",
			"options": "Warehouse",
			"width": 140
		},
		{
			"label": _("BOM (Template Required Item)"),
			"fieldname": "bom_no",
			"fieldtype": "Link",
			"options": "BOM",
			"width": 180
		},
		{
			"label": _("Production Quantity"),
			"fieldname": "production_qty",
			"fieldtype": "Float",
			"width": 120
		},
		{
			"label": _("Total Required Quantity"),
			"fieldname": "total_required_qty",
			"fieldtype": "Float",
			"width": 140
		},
		{
			"label": _("Reserved Quantity"),
			"fieldname": "reserved_qty",
			"fieldtype": "Float",
			"width": 120
		},
		{
			"label": _("Reserved Warehouse"),
			"fieldname": "reserved_warehouse",
			"fieldtype": "Link",
			"options": "Warehouse",
			"width": 140
		},
		{
			"label": _("Purchased Required Quantity"),
			"fieldname": "purchased_required_qty",
			"fieldtype": "Float",
			"width": 160
		},
		{
			"label": _("MO Required"),
			"fieldname": "mo_required",
			"fieldtype": "Float",
			"width": 110
		},
		{
			"label": _("Material Request"),
			"fieldname": "material_request",
			"fieldtype": "Link",
			"options": "Material Request",
			"width": 140
		},
		{
			"label": _("Material Request Warehouse"),
			"fieldname": "material_request_warehouse",
			"fieldtype": "Link",
			"options": "Warehouse",
			"width": 160
		},
		{
			"label": _("All Warehouse Availability"),
			"fieldname": "all_warehouse_availability",
			"fieldtype": "Float",
			"width": 150
		},
		{
			"label": _("Available After Reservation"),
			"fieldname": "available_after_reservation",
			"fieldtype": "Float",
			"width": 160
		}
	]

def get_data(filters):
	conditions = []
	values = {}
	
	if filters.get("company"):
		conditions.append("wo.company = %(company)s")
		values["company"] = filters.get("company")
		
	if filters.get("work_order"):
		conditions.append("wo.name = %(work_order)s")
		values["work_order"] = filters.get("work_order")
		
	if filters.get("bom_no"):
		conditions.append("wo.bom_no = %(bom_no)s")
		values["bom_no"] = filters.get("bom_no")
		
	if filters.get("status"):
		conditions.append("wo.status = %(status)s")
		values["status"] = filters.get("status")
		
	if filters.get("from_date"):
		conditions.append("wo.planned_start_date >= %(from_date)s")
		values["from_date"] = filters.get("from_date")
		
	if filters.get("to_date"):
		conditions.append("wo.planned_start_date <= %(to_date)s")
		values["to_date"] = filters.get("to_date")
		
	if filters.get("item_code"):
		conditions.append("woi.item_code = %(item_code)s")
		values["item_code"] = filters.get("item_code")
		
	condition_str = " AND ".join(conditions) if conditions else "1=1"
	
	raw_data = frappe.db.sql(f"""
		SELECT
			wo.name as work_order,
			bom.custom_bom_type as bom_variant,
			wo.naming_series as has_series,
			woi.item_code as item_code,
			woi.item_name as item_name,
			woi.source_warehouse as source_warehouse,
			wo.bom_no as bom_no,
			wo.qty as production_qty,
			woi.required_qty as total_required_qty,
			woi.required_qty as mo_required
		FROM
			`tabWork Order` wo
		INNER JOIN
			`tabWork Order Item` woi ON woi.parent = wo.name
		LEFT JOIN
			`tabBOM` bom ON bom.name = wo.bom_no
		WHERE
			wo.docstatus < 2 AND {condition_str}
		ORDER BY
			wo.name DESC, woi.idx ASC
	""", values, as_dict=True)
	
	processed_data = []
	for row in raw_data:
		item_code = row["item_code"]
		source_warehouse = row["source_warehouse"]
		wo_name = row["work_order"]
		
		# 1. Reserved Quantity & Reserved Warehouse from Stock Reservation Entry
		sre = frappe.db.sql("""
			SELECT
				SUM(reserved_qty) as reserved_qty,
				warehouse
			FROM
				`tabStock Reservation Entry`
			WHERE
				voucher_type = 'Work Order'
				AND voucher_no = %s
				AND item_code = %s
				AND status not in ('Cancelled', 'Delivered')
			GROUP BY
				warehouse
		""", (wo_name, item_code), as_dict=True)
		
		if sre and sre[0].get("reserved_qty"):
			reserved_qty = sre[0]["reserved_qty"]
			reserved_warehouse = sre[0]["warehouse"]
		else:
			# Fallback: check Bin for reserved_qty_for_production
			bin_reserved = frappe.db.get_value("Bin", {"item_code": item_code, "warehouse": source_warehouse}, "reserved_qty_for_production")
			reserved_qty = bin_reserved or 0.0
			reserved_warehouse = source_warehouse if reserved_qty > 0 else ""
			
		# 2. Actual Qty at Source Warehouse
		actual_qty = 0.0
		if source_warehouse:
			actual_qty = frappe.db.get_value("Bin", {"item_code": item_code, "warehouse": source_warehouse}, "actual_qty") or 0.0
			
		# 3. All Warehouse Availability
		all_wh_avail = frappe.db.get_value("Bin", {"item_code": item_code}, "sum(actual_qty)") or 0.0
		
		# 4. Material Request
		mr_item = frappe.db.sql("""
			SELECT
				parent as mr_name,
				warehouse as mr_warehouse
			FROM
				`tabMaterial Request Item`
			WHERE
				work_order = %s
				AND item_code = %s
				AND docstatus < 2
			LIMIT 1
		""", (wo_name, item_code), as_dict=True)
		
		if mr_item:
			material_request = mr_item[0]["mr_name"]
			material_request_warehouse = mr_item[0]["mr_warehouse"]
		else:
			material_request = ""
			material_request_warehouse = ""
			
		# 5. Calculations
		required_qty = row["total_required_qty"] or 0.0
		purchased_required_qty = max(0.0, required_qty - actual_qty)
		available_after_reservation = actual_qty - reserved_qty
		
		row["reserved_qty"] = reserved_qty
		row["reserved_warehouse"] = reserved_warehouse
		row["purchased_required_qty"] = purchased_required_qty
		row["material_request"] = material_request
		row["material_request_warehouse"] = material_request_warehouse
		row["all_warehouse_availability"] = all_wh_avail
		row["available_after_reservation"] = available_after_reservation
		
		processed_data.append(row)
		
	return processed_data
