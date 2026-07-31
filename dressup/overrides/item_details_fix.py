import frappe
from erpnext.stock.get_item_details import get_item_details as _original_get_item_details


@frappe.whitelist()
def get_item_details(args=None, doc=None, for_validate=False, overwrite_warehouse=True, **kwargs):
    """
    Compatibility shim: ensures that whether the client sends 'args' or 'ctx',
    it gets passed correctly to ERPNext's original `get_item_details(args, doc, ...)`.
    """
    if "ctx" in kwargs and not args:
        args = kwargs.pop("ctx")

    if args is None and "args" in kwargs:
        args = kwargs.pop("args")

    return _original_get_item_details(
        args=args,
        doc=doc,
        for_validate=for_validate,
        overwrite_warehouse=overwrite_warehouse,
        **kwargs
    )

