# Copyright (c) 2024, DressUp and contributors
# For license information, please see license.txt

from frappe import _

def get_data():
	return {
		'fieldname': 'pre_production_sample',
		'non_standard_fieldnames': {
			'Quality Inspection': 'reference_name'
		},
		'transactions': [
			{
				'label': _('Quality'),
				'items': ['Quality Inspection']
			},
			{
				'label': _('Manufacturing'),
				'items': ['BOM', 'Work Order']
			}
		]
	}
