from frappe import _


def get_data():
	return {
		"fieldname": "custom_rented_asset",
		"non_standard_fieldnames": {
			"Payment Entry": "custom_rented_asset",
			"Journal Entry": "custom_rented_asset",
		},
		"transactions": [
			{
				"label": _("Payments"),
				"items": ["Payment Entry"],
			},
			{
				"label": _("Maintenance"),
				"items": ["Asset Maintenance Log"],
			},
			{
				"label": _("Agreement"),
				"items": ["Rent Agreement Renewal"],
			},
		],
	}
