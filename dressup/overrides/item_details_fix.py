import frappe
from erpnext.stock.get_item_details import get_item_details as _original_get_item_details


@frappe.whitelist()
def get_item_details(args=None, ctx=None, doc=None, for_validate=False, overwrite_warehouse=True, **kwargs):
    """
    Compatibility shim: client may send either 'args' (old) or 'ctx' (ERPNext 16 core).
    Enriches item context with header fields from 'doc' and fallbacks so
    price list rates are properly fetched for Sales Order and other doctypes.
    """
    payload = ctx if ctx is not None else args
    if isinstance(payload, str):
        payload = frappe.parse_json(payload)
    if not payload:
        frappe.throw("Missing item context for get_item_details")

    if not isinstance(payload, dict):
        payload = dict(payload)

    # Parse parent document if passed
    doc_dict = {}
    if doc:
        if isinstance(doc, str):
            doc_dict = frappe.parse_json(doc) or {}
        elif isinstance(doc, dict):
            doc_dict = doc
        elif hasattr(doc, "as_dict"):
            doc_dict = doc.as_dict()

    # Populate missing header attributes in payload from parent doc
    if doc_dict:
        if not payload.get("customer") and (doc_dict.get("customer") or doc_dict.get("party_name")):
            payload["customer"] = doc_dict.get("customer") or doc_dict.get("party_name")
        if not payload.get("selling_price_list") and doc_dict.get("selling_price_list"):
            payload["selling_price_list"] = doc_dict.get("selling_price_list")
        if not payload.get("price_list"):
            payload["price_list"] = (
                doc_dict.get("selling_price_list")
                or doc_dict.get("buying_price_list")
                or doc_dict.get("price_list")
            )
        if not payload.get("currency") and doc_dict.get("currency"):
            payload["currency"] = doc_dict.get("currency")
        if not payload.get("company") and doc_dict.get("company"):
            payload["company"] = doc_dict.get("company")
        if not payload.get("transaction_date"):
            payload["transaction_date"] = doc_dict.get("transaction_date") or doc_dict.get("posting_date")
        if not payload.get("conversion_rate") and doc_dict.get("conversion_rate"):
            payload["conversion_rate"] = doc_dict.get("conversion_rate")
        if not payload.get("plc_conversion_rate") and doc_dict.get("plc_conversion_rate"):
            payload["plc_conversion_rate"] = doc_dict.get("plc_conversion_rate")

    # Ensure price_list is normalized
    if not payload.get("price_list"):
        payload["price_list"] = payload.get("selling_price_list") or payload.get("buying_price_list")

    # Fallback for Sales Order if price_list is missing
    doctype = payload.get("doctype") or doc_dict.get("doctype")
    if doctype == "Sales Order" and not payload.get("price_list"):
        customer = payload.get("customer")
        if customer:
            payload["price_list"] = frappe.db.get_value("Customer", customer, "default_price_list")
        if not payload.get("price_list"):
            payload["price_list"] = frappe.get_single_value("Selling Settings", "selling_price_list")

    return _original_get_item_details(
        payload,
        doc=doc,
        for_validate=for_validate,
        overwrite_warehouse=overwrite_warehouse,
    )