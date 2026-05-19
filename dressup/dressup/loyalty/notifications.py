# dressup/dressup/loyalty/notifications.py

import frappe


def send_enrollment_notification(customer_name):
	"""Customer নতুন enroll হলে।"""
	customer = frappe.db.get_value(
		"Customer",
		customer_name,
		["customer_name", "mobile_no"],
		as_dict=True,
	)
	message = (
		f"অভিনন্দন {customer.customer_name}! "
		f"আপনি Dress Up Loyalty Program-এ Bronze tier-এ যোগ দিয়েছেন। "
		f"এখন থেকে প্রতিটি কেনাকাটায় পয়েন্ট অর্জন করুন।"
	)
	_send_sms(customer.mobile_no, message)


def send_tier_upgrade_notification(customer_name, old_tier, new_tier):
	"""Tier upgrade হলে।"""
	customer = frappe.db.get_value(
		"Customer",
		customer_name,
		["customer_name", "mobile_no"],
		as_dict=True,
	)
	message = (
		f"অভিনন্দন {customer.customer_name}! "
		f"আপনার tier {old_tier} থেকে {new_tier}-এ upgrade হয়েছে। "
		f"Dress Up-এ আরও বেশি সুবিধা উপভোগ করুন।"
	)
	_send_sms(customer.mobile_no, message)


def send_tier_downgrade_notification(customer_name, old_tier, new_tier):
	"""Inactivity-তে tier downgrade হলে।"""
	customer = frappe.db.get_value(
		"Customer",
		customer_name,
		["customer_name", "mobile_no"],
		as_dict=True,
	)
	message = (
		f"প্রিয় {customer.customer_name}, "
		f"৯০ দিন কেনাকাটা না করায় আপনার tier {old_tier} থেকে {new_tier}-এ "
		f"পরিবর্তিত হয়েছে। আজই কেনাকাটা করুন এবং tier ফিরে পান।"
	)
	_send_sms(customer.mobile_no, message)


def send_inactivity_warning(customer_name, days_inactive):
	"""60-day inactivity warning।"""
	customer = frappe.db.get_value(
		"Customer",
		customer_name,
		["customer_name", "mobile_no"],
		as_dict=True,
	)
	days_left = 90 - days_inactive
	message = (
		f"প্রিয় {customer.customer_name}, "
		f"আপনি {days_inactive} দিন ধরে কেনাকাটা করেননি। "
		f"আর {days_left} দিনের মধ্যে কেনাকাটা না করলে আপনার tier downgrade হবে। "
		f"Dress Up-এ আসুন!"
	)
	_send_sms(customer.mobile_no, message)


def _send_sms(mobile_no, message):
	"""
	Frappe SMS gateway ব্যবহার করে SMS পাঠাবে।
	SMS Settings-এ gateway configure করা থাকলে কাজ করবে।
	Loyalty Program-এ 'enable_notifications' অন থাকতে হবে।
	"""
	if not mobile_no:
		return
		
	# Check if notifications are enabled
	is_enabled = frappe.db.get_value("Loyalty Program", "Dress Up Loyalty Program", "enable_notifications")
	if not is_enabled:
		return

	try:
		from frappe.core.doctype.sms_settings.sms_settings import send_sms

		send_sms([mobile_no], message)
	except Exception as e:
		frappe.logger().error(
			f"[Loyalty SMS] Failed to send to {mobile_no}: {e}"
		)
