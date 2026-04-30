import frappe
from frappe import _

@frappe.whitelist()
def get_item_details(barcode):
    if not barcode:
        return None

    # Search for item by various identifiers
    # 1. Search in Item Barcode child table
    try:
        item_code = frappe.db.get_value("Item Barcode", {"barcode": barcode}, "parent")
    except Exception:
        item_code = None
    
    # 2. Search in Serial No (check if field exists)
    if not item_code and frappe.db.exists("DocType", "Serial No"):
        try:
            item_code = frappe.db.get_value("Serial No", barcode, "item_code")
        except Exception:
            # Maybe the field is 'item'?
            try:
                item_code = frappe.db.get_value("Serial No", barcode, "item")
            except Exception:
                pass
        
    # 3. Search in Batch (check if field exists)
    if not item_code and frappe.db.exists("DocType", "Batch"):
        try:
            item_code = frappe.db.get_value("Batch", barcode, "item_code")
        except Exception:
            try:
                item_code = frappe.db.get_value("Batch", barcode, "item")
            except Exception:
                pass

    # 4. Search in Item Barcode field (if any custom field exists)
    if not item_code:
        try:
            item_code = frappe.db.get_value("Item", {"barcode": barcode}, "name")
        except Exception:
            pass
    
    # 5. Check if barcode is actually the item_code (name)
    if not item_code:
        if frappe.db.exists("Item", barcode):
            item_code = barcode
            
    # 6. Search by item_name
    if not item_code:
        try:
            item_code = frappe.db.get_value("Item", {"item_name": barcode}, "name")
        except Exception:
            pass

    if not item_code:
        return None

    item = frappe.get_doc("Item", item_code)
    
    # Get stock details
    stock_details = frappe.get_all("Bin", 
        filters={"item_code": item_code, "actual_qty": [">", 0]},
        fields=["warehouse", "actual_qty as qty", "reserved_qty", "projected_qty"]
    )

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
