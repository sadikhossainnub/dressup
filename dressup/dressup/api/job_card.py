"""
dressup/dressup/api/job_card.py
Server-side whitelisted API for Job Card bulk operations.
"""

import json

import frappe
from frappe import _
from frappe.utils import now_datetime


@frappe.whitelist()
def bulk_start_job_cards(job_cards):
	"""
	Start multiple Job Cards in bulk.

	Accepts a list (or JSON string) of Job Card names.
	For each card:
	  - Skip if it already has an open time_log (no to_time) → already running
	  - Skip if status is "Completed" or "Cancelled"
	  - Otherwise append a new time_log row and set status to "Work In Progress"

	Returns a dict with three lists: started, skipped, failed.
	"""
	# Accept either a Python list or a JSON-encoded string
	if isinstance(job_cards, str):
		try:
			job_cards = json.loads(job_cards)
		except (ValueError, TypeError):
			frappe.throw(_("Invalid job_cards argument: expected a list or JSON string."))

	if not job_cards:
		frappe.throw(_("No Job Cards provided."))

	started = []
	skipped = []
	failed = []

	# Current user – used as employee proxy when no employee link is available
	current_user = frappe.session.user

	for name in job_cards:
		try:
			doc = frappe.get_doc("Job Card", name)

			# ── Skip conditions ──────────────────────────────────────────────
			# 1. Already completed or cancelled
			if doc.status in ("Completed", "Cancelled"):
				skipped.append({"name": name, "reason": f"Status is {doc.status}"})
				continue

			# 2. Already running — there is an open time_log (from_time set, to_time not set)
			is_running = any(
				(row.from_time and not row.to_time) for row in (doc.time_logs or [])
			)
			if is_running:
				skipped.append({"name": name, "reason": "Already running"})
				continue

			# ── Start the Job Card ───────────────────────────────────────────
			# Resolve employee: use the linked employee field if present, else None
			employee = getattr(doc, "employee", None) or None

			doc.append(
				"time_logs",
				{
					"employee": employee,
					"from_time": now_datetime(),
					"completed_qty": 0,
				},
			)
			doc.status = "Work In Progress"
			doc.save(ignore_permissions=False)

			started.append(name)

		except Exception as exc:
			frappe.log_error(
				title=f"Bulk Start Job Card failed: {name}",
				message=frappe.get_traceback(),
			)
			failed.append({"name": name, "error": str(exc)})

	return {"started": started, "skipped": skipped, "failed": failed}
