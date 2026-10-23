# Copyright (c) 2026, Prime Technology of Bangladesh and contributors
# For license information, please see license.txt

"""
Patch: Fix 'Unstitched Three Piece' template HTML to use <tbody>/<td> instead of
<thead>/<th> tags, which Frappe's Quill editor strips on display — causing header
rows to disappear. Also fixes conditional rendering of section headers and yardage.
"""

import frappe
from dressup.setup import DEFAULT_TEMPLATE_HTML


def execute():
	template_name = "Unstitched Three Piece"
	if not frappe.db.exists("Item Description Template", template_name):
		return

	frappe.db.set_value(
		"Item Description Template",
		template_name,
		"template_html",
		DEFAULT_TEMPLATE_HTML,
		update_modified=True,
	)
	frappe.db.commit()
	frappe.clear_cache(doctype="Item Description Template")

