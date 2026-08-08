import json
import frappe
from erpnext.controllers.accounts_controller import update_child_qty_rate as _original_update_child_qty_rate


@frappe.whitelist()
def update_child_qty_rate(parent_doctype, trans_items, parent_doctype_name, child_docname="items"):
	"""
	Override for erpnext.controllers.accounts_controller.update_child_qty_rate

	Ensures that `discount_percentage` and `discount_amount` edited in the
	"Update Items" dialog are saved directly onto child items (e.g. Sales Order Item),
	so the "Discount (%) on Price List Rate with Margin" column updates correctly.
	"""
	# Call original update_child_qty_rate
	res = _original_update_child_qty_rate(parent_doctype, trans_items, parent_doctype_name, child_docname)

	# Update discount_percentage and discount_amount on child items
	try:
		data = json.loads(trans_items) if isinstance(trans_items, str) else trans_items
		parent = frappe.get_doc(parent_doctype, parent_doctype_name)

		updated = False
		for d in data:
			docname = d.get("docname") or d.get("name")
			if not docname:
				continue

			child_row = None
			for item in parent.get(child_docname, []):
				if item.name == docname:
					child_row = item
					break

			if child_row:
				disc_pct = frappe.utils.flt(d.get("discount_percentage"))
				disc_amt = frappe.utils.flt(d.get("discount_amount"))
				price_list_rate = frappe.utils.flt(d.get("price_list_rate")) or frappe.utils.flt(child_row.price_list_rate)
				row_rate = frappe.utils.flt(d.get("rate")) or frappe.utils.flt(child_row.rate)

				# If price list rate and rate allow deriving discount
				if price_list_rate > 0 and row_rate < price_list_rate:
					derived_pct = ((price_list_rate - row_rate) / price_list_rate) * 100.0
					derived_amt = price_list_rate - row_rate
					disc_pct = disc_pct if disc_pct > 0 else derived_pct
					disc_amt = disc_amt if disc_amt > 0 else derived_amt

				field_updates = {
					"discount_percentage": disc_pct,
					"discount_amount": disc_amt,
				}
				if price_list_rate > 0:
					field_updates["price_list_rate"] = price_list_rate
				if row_rate > 0:
					field_updates["rate"] = row_rate

				frappe.db.set_value(
					child_row.doctype,
					child_row.name,
					field_updates,
					update_modified=False,
				)
				updated = True

		if updated:
			# Re-trigger extra discount check if Sales Order
			if parent_doctype == "Sales Order":
				parent.reload()
				from dressup.dressup.custom_scripts.sales_order import check_extra_discount
				check_extra_discount(parent)
				parent.save(ignore_permissions=True)

	except Exception:
		frappe.log_error(frappe.get_traceback(), "update_child_qty_rate override discount update failed")

	return res
