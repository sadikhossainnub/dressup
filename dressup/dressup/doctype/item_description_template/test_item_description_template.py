# Copyright (c) 2026, Prime Technology of Bangladesh and Contributors
# See license.txt

import unittest
import frappe
try:
	from frappe.tests.utils import FrappeTestCase
except ImportError:
	try:
		from frappe.tests import IntegrationTestCase as FrappeTestCase
	except ImportError:
		FrappeTestCase = unittest.TestCase

from dressup.dressup.doctype.item_description_template.item_description_template import (
	ItemDescriptionTemplate,
	get_rendered_description,
)

SAMPLE_TEMPLATE_HTML = """<div class="desc-wrapper">
<h4>Size Chart — {{ size_title }} ({{ item_code }})</h4>
<p>Fabric: {{ size_fabric }}</p>
{% if kameez_body or kameez_length %}
<h5>Kameez</h5>
<p>Body: {{ kameez_body }} | Length: {{ kameez_length }}</p>
{% endif %}
{% if salwar_length %}
<h5>Salwar</h5>
<p>Length: {{ salwar_length }}" ({{ (salwar_length | float / 36) | round(2) }} Yds)</p>
{% endif %}
</div>"""


class TestItemDescriptionTemplate(FrappeTestCase):
	def setUp(self):
		self.template_doc = frappe._dict({
			"doctype": "Item Description Template",
			"name": "Test Template",
			"template_name": "Test Template",
			"enabled": 1,
			"update_web_description": 1,
			"template_html": SAMPLE_TEMPLATE_HTML,
			"fields": [
				frappe._dict({"field_key": "size_title", "field_label": "Size Title", "default_value": "Standard"}),
				frappe._dict({"field_key": "size_fabric", "field_label": "Fabric", "default_value": "Cotton"}),
				frappe._dict({"field_key": "kameez_body", "field_label": "Kameez Body", "default_value": "42"}),
				frappe._dict({"field_key": "kameez_length", "field_label": "Kameez Length", "default_value": "44"}),
				frappe._dict({"field_key": "salwar_length", "field_label": "Salwar Length", "default_value": "40"}),
			]
		})

	def test_render_with_all_values(self):
		values = [
			{"field_key": "size_title", "value": "XL"},
			{"field_key": "size_fabric", "value": "Linen Silk"},
			{"field_key": "kameez_body", "value": "44"},
			{"field_key": "kameez_length", "value": "46"},
			{"field_key": "salwar_length", "value": "72"},
		]
		item = frappe._dict({"item_code": "ITEM-TEST-001", "item_name": "Test Three Piece"})

		rendered = get_rendered_description(self.template_doc, values, item)
		self.assertIn("Size Chart — XL (ITEM-TEST-001)", rendered)
		self.assertIn("Fabric: Linen Silk", rendered)
		self.assertIn("<h5>Kameez</h5>", rendered)
		self.assertIn("Body: 44 | Length: 46", rendered)
		self.assertIn("<h5>Salwar</h5>", rendered)
		self.assertIn('Length: 72" (2.0 Yds)', rendered)

	def test_render_with_some_sections_empty(self):
		# Omit salwar_length, should hide Salwar section and not crash on float math
		values = [
			{"field_key": "size_title", "value": "Medium"},
			{"field_key": "size_fabric", "value": "Cotton"},
			{"field_key": "kameez_body", "value": "38"},
			{"field_key": "kameez_length", "value": "42"},
			{"field_key": "salwar_length", "value": ""},
		]
		item = frappe._dict({"item_code": "ITEM-TEST-002"})

		rendered = get_rendered_description(self.template_doc, values, item)
		self.assertIn("Size Chart — Medium (ITEM-TEST-002)", rendered)
		self.assertIn("<h5>Kameez</h5>", rendered)
		self.assertNotIn("<h5>Salwar</h5>", rendered)

	def test_html_escaping_of_values(self):
		# User entered malicious script/HTML tags must be escaped
		values = [
			{"field_key": "size_title", "value": "<script>alert('xss')</script>"},
			{"field_key": "size_fabric", "value": '<b onclick="evil()">Cotton</b>'},
			{"field_key": "kameez_body", "value": '"><img src=x onerror=alert(1)>'},
		]
		item = frappe._dict({"item_code": "ITEM<003>"})

		rendered = get_rendered_description(self.template_doc, values, item)
		self.assertNotIn("<script>", rendered)
		self.assertNotIn('onclick="evil()"', rendered)
		self.assertNotIn("<img src=x onerror=alert(1)>", rendered)
		self.assertNotIn("ITEM<003>", rendered)
		self.assertIn("&lt;script&gt;alert(", rendered)
		self.assertIn("&lt;/script&gt;", rendered)
		self.assertIn("&lt;b onclick=&quot;evil()&quot;&gt;Cotton&lt;/b&gt;", rendered)
		self.assertIn("&lt;img src=x onerror=alert(1)&gt;", rendered)
		self.assertIn("ITEM&lt;003&gt;", rendered)

	def test_invalid_jinja_rejected(self):
		doc = ItemDescriptionTemplate()
		doc.template_name = "Bad Jinja Template"
		doc.template_html = "Hello {{ unclosed_variable "

		with self.assertRaises(frappe.ValidationError):
			doc.validate_template_syntax()

	def test_field_key_validation(self):
		doc = ItemDescriptionTemplate()
		doc.template_name = "Field Key Test"
		doc.template_html = "<p>{{ test }}</p>"

		# 1. Invalid characters (hyphen)
		doc.fields = [frappe._dict({"field_key": "invalid-key", "field_label": "Invalid Key"})]
		with self.assertRaises(frappe.ValidationError):
			doc.validate_fields()

		# 2. Starts with a number
		doc.fields = [frappe._dict({"field_key": "123_invalid", "field_label": "Starts with number"})]
		with self.assertRaises(frappe.ValidationError):
			doc.validate_fields()

		# 3. Uppercase letters
		doc.fields = [frappe._dict({"field_key": "Invalid_Key", "field_label": "Uppercase"})]
		with self.assertRaises(frappe.ValidationError):
			doc.validate_fields()

		# 4. Duplicate keys
		doc.fields = [
			frappe._dict({"field_key": "valid_key", "field_label": "Key 1"}),
			frappe._dict({"field_key": "valid_key", "field_label": "Key 2"}),
		]
		with self.assertRaises(frappe.ValidationError):
			doc.validate_fields()

		# 5. Valid keys pass
		doc.fields = [
			frappe._dict({"field_key": "valid_key_1", "field_label": "Key 1"}),
			frappe._dict({"field_key": "another_key", "field_label": "Key 2"}),
		]
		doc.validate_fields()
		self.assertEqual(len(doc.fields), 2)
