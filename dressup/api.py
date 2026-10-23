# Copyright (c) 2026, Prime Technology of Bangladesh and contributors
# For license information, please see license.txt

import json
import frappe
from frappe import _
from dressup.dressup.doctype.item_description_template.item_description_template import (
	get_rendered_description,
)


@frappe.whitelist()
def regenerate_item_descriptions(template):
	"""
	Whitelisted endpoint to enqueue bulk regeneration of Item descriptions
	for all Items assigned to the specified template.
	Permission: System Manager only.
	"""
	if "System Manager" not in frappe.get_roles():
		frappe.throw(
			_("Only System Managers can regenerate item descriptions in bulk."),
			frappe.PermissionError,
		)

	if not template or not frappe.db.exists("Item Description Template", template):
		frappe.throw(_("Item Description Template '{0}' not found.").format(template))

	frappe.enqueue(
		"dressup.api._bulk_regenerate_item_descriptions",
		queue="default",
		timeout=1800,
		template_name=template,
		user=frappe.session.user,
		now=frappe.flags.in_test,
	)

	return {
		"status": "queued",
		"message": _("Bulk regeneration for template '{0}' has been enqueued.").format(template),
	}


def _bulk_regenerate_item_descriptions(template_name, user=None):
	"""
	Background job executing bulk item description rendering.
	Uses direct database updates via frappe.db.set_value to avoid triggering
	document hooks / WooCommerce sync loops.
	"""
	template = frappe.get_doc("Item Description Template", template_name)

	items = frappe.get_all(
		"Item",
		filters={"description_template": template_name},
		fields=["name", "item_code", "item_name", "brand", "item_group"],
	)

	total = len(items)
	if total == 0:
		frappe.publish_progress(
			percent=100,
			title=_("Regenerating Item Descriptions"),
			description=_("No items found using template '{0}'").format(template_name),
			user=user,
		)
		return

	for idx, item in enumerate(items, start=1):
		# Fetch child table rows for this Item
		values = frappe.get_all(
			"Item Description Value",
			filters={"parent": item.name, "parenttype": "Item"},
			fields=["field_key", "value"],
		)

		rendered_html = get_rendered_description(
			template=template,
			values_dict=values,
			item_doc=frappe._dict(item),
		)

		update_dict = {"description": rendered_html}
		if template.update_web_description:
			update_dict["web_long_description"] = rendered_html

		# Use frappe.db.set_value to avoid full doc.save() lifecycle / WooCommerce loop
		frappe.db.set_value("Item", item.name, update_dict, update_modified=True)

		if idx % 5 == 0 or idx == total:
			percent = int((idx / total) * 100)
			frappe.publish_progress(
				percent=percent,
				title=_("Regenerating Item Descriptions"),
				description=_("Processed {0} of {1} items").format(idx, total),
				user=user,
			)
			frappe.db.commit()

	frappe.db.commit()


@frappe.whitelist()
def preview_item_description(
	template_name=None,
	template_html=None,
	values=None,
	item_code=None,
	item_name=None,
	brand=None,
	item_group=None,
):
	"""
	Whitelisted preview method that renders HTML without saving the Item document.
	"""
	if isinstance(values, str):
		try:
			values = json.loads(values)
		except Exception:
			values = []

	item_context = frappe._dict({
		"item_code": item_code or "SAMPLE-ITEM",
		"item_name": item_name or "Sample Item",
		"brand": brand or "",
		"item_group": item_group or "",
	})

	if template_html:
		template_doc = frappe._dict({
			"name": template_name or "Preview",
			"template_html": template_html,
			"fields": [],
		})
	elif template_name:
		template_doc = frappe.get_cached_doc("Item Description Template", template_name)
	else:
		frappe.throw(_("Template or Template HTML is required."))

	return get_rendered_description(
		template=template_doc,
		values_dict=values,
		item_doc=item_context,
	)

