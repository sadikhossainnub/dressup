import frappe


def execute():
	"""Add Pre Production Sample to Quality Inspection reference_type options"""
	
	# Check if property setter already exists
	existing = frappe.db.exists("Property Setter", {
		"doctype_or_field": "DocField",
		"doc_type": "Quality Inspection",
		"field_name": "reference_type",
		"property": "options"
	})
	
	if existing:
		# Update existing property setter
		property_setter = frappe.get_doc("Property Setter", existing)
		current_options = property_setter.value or ""
		if "Pre Production Sample" not in current_options:
			property_setter.value = current_options + "\nPre Production Sample"
			property_setter.save()
	else:
		# Create new property setter
		frappe.get_doc({
			"doctype": "Property Setter",
			"doctype_or_field": "DocField",
			"doc_type": "Quality Inspection",
			"field_name": "reference_type",
			"property": "options",
			"value": "\nPurchase Receipt\nPurchase Invoice\nSubcontracting Receipt\nDelivery Note\nSales Invoice\nStock Entry\nJob Card\nPre Production Sample",
			"property_type": "Text"
		}).insert()
	
	frappe.db.commit()
	print("Added Pre Production Sample to Quality Inspection reference_type options")
