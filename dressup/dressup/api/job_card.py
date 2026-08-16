"""
dressup/dressup/api/job_card.py
Server-side whitelisted API for Job Card bulk operations.
"""

import json

import frappe
from frappe import _
from frappe.utils import flt, now_datetime


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

			# ── Skip condition: only "Open" cards can be started ────────────────
			if doc.status != "Open":
				skipped.append({"name": name, "reason": f"Status is '{doc.status}' (expected Open)"})
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


@frappe.whitelist()
def bulk_complete_job_cards(job_cards):
	"""
	Complete multiple Job Cards in bulk.

	Accepts a list (or JSON string) of Job Card names.
	For each card:
	  - Skip if status is already "Completed" or "Cancelled"
	  - Close any open time_log row (to_time = now) so the card is not left running
	  - Set completed_qty on the open row to the card's for_qty (target qty)
	  - Set status to "Completed" and save

	Returns a dict with three lists: completed, skipped, failed.
	"""
	if isinstance(job_cards, str):
		try:
			job_cards = json.loads(job_cards)
		except (ValueError, TypeError):
			frappe.throw(_("Invalid job_cards argument: expected a list or JSON string."))

	if not job_cards:
		frappe.throw(_(("No Job Cards provided.")))

	completed = []
	skipped = []
	failed = []

	for name in job_cards:
		try:
			doc = frappe.get_doc("Job Card", name)

			# ── Skip condition: only "Work In Progress" cards can be completed ──
			if doc.status != "Work In Progress":
				skipped.append({"name": name, "reason": f"Status is '{doc.status}' (expected Work In Progress)"})
				continue

			now = now_datetime()

			# ── Close any open time_log rows ─────────────────────────────────
			# An open row has from_time set but no to_time
			has_open = False
			for row in doc.time_logs or []:
				if row.from_time and not row.to_time:
					row.to_time = now
					# Fill completed_qty with remaining target qty if not already set
					target_qty = flt(getattr(doc, "for_qty", 0) or 0)
					if not flt(row.completed_qty):
						row.completed_qty = target_qty
					has_open = True

			# If no open time_log exists, we still complete the card.
			# Optionally, we could add a synthetic log entry — skipped here for
			# simplicity to avoid double-counting.

			doc.status = "Completed"
			doc.save(ignore_permissions=False)

			completed.append(name)

		except Exception as exc:
			frappe.log_error(
				title=f"Bulk Complete Job Card failed: {name}",
				message=frappe.get_traceback(),
			)
			failed.append({"name": name, "error": str(exc)})

	return {"completed": completed, "skipped": skipped, "failed": failed}
