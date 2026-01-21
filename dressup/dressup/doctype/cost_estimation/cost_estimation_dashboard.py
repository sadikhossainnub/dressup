# Copyright (c) 2024, DressUp and contributors
# For license information, please see license.txt

from frappe import _

def get_data():
	return {
		'fieldname': 'tech_pack_no',
		'transactions': [
			{
				'label': _('PPS'),
				'items': ['Pre Production Sample']
			}
		]
	}
