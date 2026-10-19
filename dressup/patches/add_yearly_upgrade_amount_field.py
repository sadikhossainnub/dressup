# Copyright (c) 2026, Prime Technology of Bangladesh and contributors
# For license information, please see license.txt

"""
Patch: Add yearly_upgrade_amount custom field to Loyalty Program Collection
and create default Loyalty Tier Upgrade Settings document.
"""

import frappe


def execute():
	from dressup.setup import (
		add_yearly_upgrade_amount_custom_field,
		create_loyalty_program_summary_report,
		create_loyalty_tier_upgrade_settings,
	)

	add_yearly_upgrade_amount_custom_field()
	create_loyalty_program_summary_report()
	create_loyalty_tier_upgrade_settings()

