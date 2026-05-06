import frappe

def set_from_voucher_type():
    options = frappe.get_meta("Stock Reservation Entry").get_field("from_voucher_type").options
    if "Cost Estimation" not in (options or ""):
        new_options = (options or "") + "\nCost Estimation"
        frappe.make_property_setter({
            "doctype_or_field": "DocField",
            "doc_type": "Stock Reservation Entry",
            "field_name": "from_voucher_type",
            "property": "options",
            "value": new_options,
            "property_type": "Text"
        })
        return f"Added Cost Estimation to options: {new_options}"
    return "Already exists"
