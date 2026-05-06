# Copyright (c) 2024, DressUp and contributors
# For license information, please see license.txt

from frappe import _

def get_data():
	return {
		'fieldname': 'cost_estimation',
		'non_standard_fieldnames': {
			'Pre Production Sample': 'cost_estimation'
		},
		'transactions': [
			{
				'label': _('PPS'),
				'items': ['Pre Production Sample']
			}
		]
	}
