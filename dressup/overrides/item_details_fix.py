import frappe
from erpnext.stock.get_item_details import get_item_details as _original_get_item_details


@frappe.whitelist()
def get_item_details(args=None, doc=None, for_validate=False, overwrite_warehouse=True, **kwargs):
    """
    Compatibility shim: client sends 'args', ERPNext 16 core function
    expects first positional param named 'ctx'. Passing positionally
    avoids the naming mismatch entirely.
    """
    return _original_get_item_details(
        args,   # positional -> maps to ctx regardless of param name
        doc=doc,
        for_validate=for_validate,
        overwrite_warehouse=overwrite_warehouse,
    )