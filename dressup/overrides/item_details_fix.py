import frappe
from erpnext.stock.get_item_details import get_item_details as _original_get_item_details


@frappe.whitelist()
def get_item_details(*args, **kwargs):
    """
    Compatibility shim: older client JS calls (e.g. sales_common.js, update_child_items)
    POST the payload under the key 'args', but newer ERPNext (>=16.x) may expect the
    whitelisted `get_item_details` function to receive it as `ctx`.

    This override normalises both directions so the call works regardless of
    which parameter name the client or server uses.

    Fixes: TypeError: get_item_details() missing 1 required positional argument: 'ctx'
    Ref: https://github.com/frappe/erpnext/issues/51345
    """
    # Client sent 'args' but original function expects 'ctx'
    if "args" in kwargs and "ctx" not in kwargs:
        kwargs["ctx"] = kwargs.pop("args")

    # Client sent 'ctx' but original function expects 'args'
    if "ctx" in kwargs and "args" not in kwargs:
        kwargs["args"] = kwargs.pop("ctx")

    # Positional arg fallback: if the first positional is the payload,
    # ensure it maps to whichever key the original expects
    if args and "args" not in kwargs and "ctx" not in kwargs:
        args = list(args)
        kwargs["args"] = args.pop(0)

    return _original_get_item_details(*args, **kwargs)
