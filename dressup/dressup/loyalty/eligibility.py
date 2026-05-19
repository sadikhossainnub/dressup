# dressup/dressup/loyalty/eligibility.py

import frappe
from frappe.utils import getdate, today, get_first_day, get_last_day

LOYALTY_PROGRAM = "Dress Up Loyalty Program"
ELIGIBILITY_THRESHOLD = 10000  # ৳10,000


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

	if monthly_total >= ELIGIBILITY_THRESHOLD:
		_enroll_customer(customer)


def _enroll_customer(customer):
	"""Customer-কে loyalty program-এ enroll করে।"""
	frappe.db.set_value(
		"Customer",
		customer.name,
		{
			"loyalty_program": LOYALTY_PROGRAM,
			"loyalty_eligible": 1,
			"loyalty_enrolled_date": today(),
			"last_purchase_date": today(),
		},
	)
	frappe.db.commit()

	# Notification পাঠাও
	from dressup.dressup.loyalty.notifications import send_enrollment_notification

	send_enrollment_notification(customer.name)

	frappe.logger().info(
		f"[Loyalty] Customer {customer.name} enrolled in {LOYALTY_PROGRAM}"
	)


def run_monthly_eligibility_check():
	"""
	Monthly scheduler job।
	পুরো customer list scan করে যারা eligible কিন্তু
	এখনো enroll হয়নি তাদের check করে।
	"""
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

		if monthly_total >= ELIGIBILITY_THRESHOLD:
			customer = frappe.get_doc("Customer", c.name)
			_enroll_customer(customer)
