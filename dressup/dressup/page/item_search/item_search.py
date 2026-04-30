import frappe
from frappe import _

@frappe.whitelist()
def get_item_details(barcode):
    if not barcode:
        return None

    # Search for item by barcode or item_code
    # 1. Search in Item Barcode child table
    item_code = frappe.db.get_value("Item Barcode", {"barcode": barcode}, "parent")
    
    # 2. Search in Item Barcode field (if any custom field exists)
    if not item_code:
        item_code = frappe.db.get_value("Item", {"barcode": barcode}, "name")
    
    # 3. Check if barcode is actually the item_code (name)
    if not item_code:
        if frappe.db.exists("Item", barcode):
            item_code = barcode
            
    # 4. Search by item_name (fuzzy or exact)
    if not item_code:
        item_code = frappe.db.get_value("Item", {"item_name": barcode}, "name")

    if not item_code:
        return None

    item = frappe.get_doc("Item", item_code)
    
    # Get stock details
    stock_details = frappe.db.sql("""
        SELECT 
            warehouse, 
            actual_qty as qty,
            reserved_qty,
            projected_qty
        FROM 
            tabBin 
        WHERE 
            item_code = %s AND actual_qty > 0
    """, (item_code,), as_dict=1)

    return {
        "item_code": item.item_code,
        "item_name": item.item_name,
        "description": item.description,
        "image": item.image,
        "stock": stock_details,
        "uom": item.stock_uom,
        "brand": item.brand,
        "item_group": item.item_group
    }
