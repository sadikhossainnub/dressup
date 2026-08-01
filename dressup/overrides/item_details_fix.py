import frappe
from erpnext.stock.get_item_details import get_item_details as _original_get_item_details


@frappe.whitelist()
def get_item_details(args=None, ctx=None, doc=None, for_validate=False, overwrite_warehouse=True, **kwargs):
    """
    Compatibility shim: client may send either 'args' (old) or 'ctx' (ERPNext 16 core).
    Custom logic (if any) applies ONLY to Sales Order; all other doctypes
    (Purchase Order, Material Request, Stock Entry, Delivery Note, etc.)
    pass straight through to core with no extra behavior.
    """
    payload = ctx if ctx is not None else args
    if isinstance(payload, str):
        payload = frappe.parse_json(payload)
    if not payload:
        frappe.throw("Missing item context for get_item_details")

    doctype = payload.get("doctype")

    if doctype == "Sales Order":
        # ---- Sales Order-specific logic goes here (if/when needed) ----
        pass

    return _original_get_item_details(
        payload,
        doc=doc,
        for_validate=for_validate,
        overwrite_warehouse=overwrite_warehouse,
    )