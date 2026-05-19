# dressup/setup_custom_fields.py

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


CUSTOM_FIELDS = {
	"Customer": [
		{
			"fieldname": "loyalty_eligible",
			"label": "Loyalty Eligible",
			"fieldtype": "Check",
			"insert_after": "loyalty_program",
			"default": "0",
			"read_only": 1,
			"description": "Auto set when customer spends ৳10,000 in any 1 month",
			"module": "DressUp",
		},
		{
			"fieldname": "loyalty_enrolled_date",
			"label": "Loyalty Enrolled Date",
			"fieldtype": "Date",
			"insert_after": "loyalty_eligible",
			"read_only": 1,
			"module": "DressUp",
		},
		{
			"fieldname": "last_purchase_date",
			"label": "Last Purchase Date",
			"fieldtype": "Date",
			"insert_after": "loyalty_enrolled_date",
			"read_only": 1,
			"module": "DressUp",
		},
		{
			"fieldname": "inactivity_warned",
			"label": "Inactivity Warning Sent",
			"fieldtype": "Check",
			"insert_after": "last_purchase_date",
			"default": "0",
			"read_only": 1,
			"description": "60-day inactivity warning sent হয়েছে কিনা",
			"module": "DressUp",
		},
	],
	"Loyalty Program": [
		{
			"fieldname": "enable_notifications",
			"label": "Enable SMS Notifications",
			"fieldtype": "Check",
			"insert_after": "expiry_duration",
			"default": "1",
			"description": "Send SMS to customers on enrollment, tier upgrade, downgrade, and inactivity warning.",
			"module": "DressUp",
		}
	]
}


def execute():
	"""Create custom fields for the Loyalty Program on Customer DocType."""
	create_custom_fields(CUSTOM_FIELDS, update=True)
	frappe.db.commit()
