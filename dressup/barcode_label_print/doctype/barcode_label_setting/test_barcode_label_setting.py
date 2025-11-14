import frappe
import unittest


class TestBarcodeLabelSetting(unittest.TestCase):
	def test_label_dimensions_validation(self):
		doc = frappe.get_doc({
			"doctype": "Barcode Label Setting",
			"label_name": "Test Label",
			"label_width": 0,
			"label_height": 50
		})
		with self.assertRaises(frappe.ValidationError):
			doc.insert()