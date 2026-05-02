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

    # Get reservation details
    reservations = get_reservation_details(item_code)

    # Get item prices
    prices = get_item_prices(item_code)

    return {
        "item_code": item.item_code,
        "item_name": item.item_name,
        "description": item.description,
        "image": item.image,
        "stock": stock_details,
        "uom": item.stock_uom,
        "brand": item.brand,
        "item_group": item.item_group,
        "reservations": reservations,
        "prices": prices
    }


def get_item_prices(item_code):
    """Get all active prices for an item from Item Price doctype."""
    today = frappe.utils.today()

    try:
        price_list = frappe.get_all(
            "Item Price",
            filters={
                "item_code": item_code,
                "valid_from": ["<=", today],
            },
            or_filters={
                "valid_upto": [">=", today],
                "valid_upto": ["is", "not set"],
            },
            fields=[
                "price_list", "price_list_rate", "currency",
                "selling", "buying", "uom",
                "valid_from", "valid_upto"
            ],
            order_by="selling desc, price_list_rate asc"
        )
    except Exception:
        # Fallback: fetch without date filters
        price_list = frappe.get_all(
            "Item Price",
            filters={"item_code": item_code},
            fields=[
                "price_list", "price_list_rate", "currency",
                "selling", "buying", "uom",
                "valid_from", "valid_upto"
            ],
            order_by="selling desc, price_list_rate asc"
        )

    prices = []
    for p in price_list:
        price_type = "Selling" if p.selling else ("Buying" if p.buying else "N/A")
        prices.append({
            "price_list": p.price_list or "",
            "rate": p.price_list_rate or 0,
            "currency": p.currency or "",
            "type": price_type,
            "uom": p.uom or "",
            "valid_from": str(p.valid_from) if p.valid_from else "",
            "valid_upto": str(p.valid_upto) if p.valid_upto else "",
        })

    return prices


def get_reservation_details(item_code):
    """Get stock reservation details for an item from Stock Reservation Entry and Sales Orders."""
    reservations = []

    # 1. Get from Stock Reservation Entry (if doctype exists)
    if frappe.db.exists("DocType", "Stock Reservation Entry"):
        try:
            sre_list = frappe.get_all(
                "Stock Reservation Entry",
                filters={
                    "item_code": item_code,
                    "status": ["in", ["Reserved", "Partially Reserved", "Partially Delivered"]],
                    "docstatus": 1
                },
                fields=[
                    "name", "voucher_type", "voucher_no", "warehouse",
                    "reserved_qty", "delivered_qty", "status",
                    "creation", "owner"
                ],
                order_by="creation desc"
            )

            for sre in sre_list:
                remaining = (sre.reserved_qty or 0) - (sre.delivered_qty or 0)
                if remaining > 0:
                    customer = ""
                    if sre.voucher_type == "Sales Order" and sre.voucher_no:
                        customer = frappe.db.get_value("Sales Order", sre.voucher_no, "customer_name") or ""

                    # Get full name of the user who created the reservation
                    reserved_by = frappe.db.get_value("User", sre.owner, "full_name") or sre.owner or ""

                    reservations.append({
                        "source": "Stock Reservation",
                        "reference_type": sre.voucher_type or "",
                        "reference_name": sre.voucher_no or "",
                        "warehouse": sre.warehouse or "",
                        "reserved_qty": sre.reserved_qty or 0,
                        "delivered_qty": sre.delivered_qty or 0,
                        "remaining_qty": remaining,
                        "customer": customer,
                        "reserved_by": reserved_by,
                        "status": sre.status,
                        "date": str(sre.creation.date()) if sre.creation else ""
                    })
        except Exception:
            pass

    # 2. If no Stock Reservation Entries, fall back to Sales Order Items with pending delivery
    if not reservations:
        try:
            pending_so_items = frappe.db.sql("""
                SELECT
                    so.name as sales_order,
                    so.customer_name,
                    so.transaction_date,
                    so.owner as so_owner,
                    soi.warehouse,
                    soi.qty,
                    soi.delivered_qty,
                    (soi.qty - soi.delivered_qty) as pending_qty,
                    soi.stock_reserved_qty
                FROM `tabSales Order Item` soi
                JOIN `tabSales Order` so ON so.name = soi.parent
                WHERE soi.item_code = %s
                    AND so.docstatus = 1
                    AND so.status NOT IN ('Completed', 'Cancelled', 'Closed')
                    AND soi.delivered_qty < soi.qty
                ORDER BY so.transaction_date DESC
            """, item_code, as_dict=True)

            for row in pending_so_items:
                reserved_by = frappe.db.get_value("User", row.so_owner, "full_name") or row.so_owner or ""

                reservations.append({
                    "source": "Sales Order",
                    "reference_type": "Sales Order",
                    "reference_name": row.sales_order,
                    "warehouse": row.warehouse or "",
                    "reserved_qty": row.qty or 0,
                    "delivered_qty": row.delivered_qty or 0,
                    "remaining_qty": row.pending_qty or 0,
                    "customer": row.customer_name or "",
                    "reserved_by": reserved_by,
                    "status": "Pending Delivery",
                    "date": str(row.transaction_date) if row.transaction_date else ""
                })
        except Exception:
            pass

    return reservations


@frappe.whitelist()
def get_suggestions(query):
    if not query or len(query) < 1:
        return []

    # 1. Search by Item Code or Item Name using SQL for better OR handling
    items = frappe.db.sql("""
        SELECT name, item_name 
        FROM `tabItem` 
        WHERE (name LIKE %s OR item_name LIKE %s)
          AND disabled = 0 
          AND has_variants = 0
        LIMIT 10
    """, (f"%{query}%", f"%{query}%"), as_dict=True)

    suggestions = []
    for item in items:
        suggestions.append({
            "value": item.name,
            "label": f"{item.item_name} ({item.name})",
            "type": "Item"
        })

    # 2. Search by Barcode - join with Item to ensure it's active
    barcodes = frappe.db.sql("""
        SELECT ib.barcode, ib.parent as item_code
        FROM `tabItem Barcode` ib
        JOIN `tabItem` i ON ib.parent = i.name
        WHERE ib.barcode LIKE %s
          AND i.disabled = 0
        LIMIT 5
    """, (f"%{query}%",), as_dict=True)

    for b in barcodes:
        # Avoid duplicate item suggestions
        if not any(s["value"] == b.barcode for s in suggestions):
            suggestions.append({
                "value": b.barcode,
                "label": f"Barcode: {b.barcode} ({b.item_code})",
                "type": "Barcode"
            })

    return suggestions
