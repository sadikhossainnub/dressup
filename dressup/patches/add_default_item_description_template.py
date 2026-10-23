# Copyright (c) 2026, Prime Technology of Bangladesh and contributors
# For license information, please see license.txt

"""
Patch: Add Item Description Template custom fields and seed the default
'Unstitched Three Piece' template if it does not already exist.
"""

import frappe
from dressup.setup import (
	add_item_description_template_custom_fields,
	create_default_item_description_template,
)


def execute():
	add_item_description_template_custom_fields()
	create_default_item_description_template()

