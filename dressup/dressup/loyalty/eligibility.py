# dressup/dressup/loyalty/eligibility.py

import frappe
from frappe.utils import getdate, today, get_first_day, get_last_day

from dressup.dressup.loyalty import get_loyalty_program, get_eligibility_threshold


def check_eligibility_on_invoice(invoice_doc):
	"""
	Sales Invoice submit হলে call হবে।
	Customer already eligible হলে skip।
	না হলে current month-এর total spend check করবে।
	"""
	customer = frappe.get_doc("Customer", invoice_doc.customer)

	# Already enrolled → skip
	if customer.get("loyalty_eligible"):
		return

	loyalty_program = get_loyalty_program()
	if not loyalty_program:
		return

	threshold = get_eligibility_threshold(loyalty_program)

	# Threshold 0 মানে no gate → সাথে সাথে enroll
	if not threshold:
		_enroll_customer(customer, loyalty_program)
		return

	# Current month total spend calculate
	month_start = get_first_day(getdate(today()))
	month_end = get_last_day(getdate(today()))

	monthly_total = frappe.db.sql(
		"""
		SELECT IFNULL(SUM(grand_total), 0)
		FROM `tabSales Invoice`
		WHERE customer = %s
		  AND docstatus = 1
		  AND posting_date BETWEEN %s AND %s
		""",
		(invoice_doc.customer, month_start, month_end),
	)[0][0]

	if monthly_total >= threshold:
		_enroll_customer(customer, loyalty_program)


def _enroll_customer(customer, loyalty_program=None):
	"""Customer-কে loyalty program-এ enroll করে।"""
	if not loyalty_program:
		loyalty_program = get_loyalty_program()

	if not loyalty_program:
		frappe.logger().warning(
			"[Loyalty] No Loyalty Program found in the system. "
			"Please create a Loyalty Program first."
		)
		return

	frappe.db.set_value(
		"Customer",
		customer.name,
		{
			"loyalty_program": loyalty_program,
			"loyalty_eligible": 1,
			"loyalty_enrolled_date": today(),
			"last_purchase_date": today(),
		},
	)
	frappe.db.commit()

	# Notification পাঠাও
	from dressup.dressup.loyalty.notifications import send_enrollment_notification

	send_enrollment_notification(customer.name, loyalty_program)

	frappe.logger().info(
		f"[Loyalty] Customer {customer.name} enrolled in {loyalty_program}"
	)


def run_monthly_eligibility_check():
	"""
	Monthly scheduler job।
	পুরো customer list scan করে যারা eligible কিন্তু
	এখনো enroll হয়নি তাদের check করে।
	"""
	loyalty_program = get_loyalty_program()
	if not loyalty_program:
		return

	threshold = get_eligibility_threshold(loyalty_program)

	# No threshold → কোনো monthly check দরকার নেই
	if not threshold:
		return

	not_enrolled = frappe.get_all(
		"Customer",
		filters={"loyalty_eligible": 0},
		fields=["name"],
	)

	prev_month_start = get_first_day(
		frappe.utils.add_months(getdate(today()), -1)
	)
	prev_month_end = get_last_day(
		frappe.utils.add_months(getdate(today()), -1)
	)

	for c in not_enrolled:
		monthly_total = frappe.db.sql(
			"""
			SELECT IFNULL(SUM(grand_total), 0)
			FROM `tabSales Invoice`
			WHERE customer = %s
			  AND docstatus = 1
			  AND posting_date BETWEEN %s AND %s
			""",
			(c.name, prev_month_start, prev_month_end),
		)[0][0]

		if monthly_total >= threshold:
			customer = frappe.get_doc("Customer", c.name)
			_enroll_customer(customer, loyalty_program)
