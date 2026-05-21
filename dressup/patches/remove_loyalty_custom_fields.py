import frappe

def execute():
	"""Remove loyalty-related custom fields and clear cache."""
	custom_fields_to_remove = [
		("Customer", "loyalty_eligible"),
		("Customer", "loyalty_enrolled_date"),
		("Customer", "last_purchase_date"),
		("Customer", "inactivity_warned"),
		("Loyalty Program", "eligibility_threshold"),
		("Loyalty Program", "enable_notifications"),
		("Loyalty Program Collection", "max_spent")
	]
	
	for dt, fieldname in custom_fields_to_remove:
		custom_field_name = f"{dt}-{fieldname}"
		if frappe.db.exists("Custom Field", custom_field_name):
			frappe.delete_doc("Custom Field", custom_field_name, ignore_permissions=True, force=True)
			
	# Cleanup property setters for the removed fields
	frappe.db.sql("""DELETE FROM `tabProperty Setter` 
		WHERE doc_type='Customer' 
		AND field_name IN ('loyalty_eligible', 'loyalty_enrolled_date', 'last_purchase_date', 'inactivity_warned')""")
	
	frappe.db.sql("""DELETE FROM `tabProperty Setter` 
		WHERE doc_type='Loyalty Program' 
		AND field_name IN ('eligibility_threshold', 'enable_notifications')""")
		
	frappe.db.sql("""DELETE FROM `tabProperty Setter` 
		WHERE doc_type='Loyalty Program Collection' 
		AND field_name IN ('max_spent')""")
	
	frappe.clear_cache()
