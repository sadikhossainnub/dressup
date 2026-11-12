import inspect
import frappe
from erpnext.stock.utils import scan_barcode as _original_scan_barcode
try:
	from erpnext.stock.utils import _update_item_info
except ImportError:
	_update_item_info = None


@frappe.whitelist()
def scan_barcode(search_value: str, ctx: dict | str | None = None, **kwargs):
	"""
	Override for erpnext.stock.utils.scan_barcode

	Extends standard barcode scanner logic:
	1. Calls ERPNext's original scan_barcode safely, dynamically adapting to its
	   exact parameter signature across different ERPNext/Frappe releases.
	2. If not found in Barcode/Serial/Batch/Warehouse, checks directly in the Item
	   DocType by item_code or name, allowing direct item code scanning without
	   requiring an Item Barcode child table entry.
	"""
	# Prepare arguments matching the underlying _original_scan_barcode signature
	passed_args = {"search_value": search_value}
	if ctx is not None:
		passed_args["ctx"] = ctx
	passed_args.update(kwargs)

	try:
		sig = inspect.signature(_original_scan_barcode)
		call_kwargs = {k: v for k, v in passed_args.items() if k in sig.parameters}
		result = _original_scan_barcode(**call_kwargs)
	except TypeError:
		# Fallback if inspect fails or typing wrapper interferes
		if "item_code" in passed_args:
			passed_args.pop("item_code", None)
		result = _original_scan_barcode(search_value, ctx=ctx)
	except Exception:
		result = None

	if result:
		return result

	# If no barcode/serial/batch/warehouse match found, check directly in Item table
	if search_value:
		item_filter = {"name": search_value, "disabled": 0}
		matched_item = frappe.db.get_value("Item", item_filter, ["name", "stock_uom"], as_dict=True)

		if not matched_item:
			matched_item = frappe.db.get_value(
				"Item",
				{"item_code": search_value, "disabled": 0},
				["name", "stock_uom"],
				as_dict=True,
			)

		if matched_item:
			candidate = {
				"item_code": matched_item.name,
				"uom": matched_item.stock_uom,
			}
			# Enrich with context info if helper is available
			if _update_item_info:
				parsed_ctx = frappe.parse_json(ctx) if isinstance(ctx, str) else (ctx or {})
				try:
					_update_item_info(candidate, parsed_ctx)
				except Exception:
					pass

			return candidate

	return {}
