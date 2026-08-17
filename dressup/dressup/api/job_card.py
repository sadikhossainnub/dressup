"""
dressup/dressup/api/job_card.py
Server-side whitelisted API for Job Card bulk operations.
"""

import json

import frappe
from frappe import _
from frappe.utils import flt, now_datetime


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _parse_list(value, param_name="value"):
	"""Accept a Python list or a JSON-encoded string; return a list."""
	if isinstance(value, str):
		try:
			value = json.loads(value)
		except (ValueError, TypeError):
			frappe.throw(_(f"Invalid {param_name}: expected a list or JSON string."))
	return value or []


# ─────────────────────────────────────────────────────────────────────────────
# Bulk Start
# ─────────────────────────────────────────────────────────────────────────────

@frappe.whitelist()
def bulk_start_job_cards(job_cards):
	"""
	Start multiple Job Cards in bulk.

	Only cards with status "Open" are processed; others are skipped.
	Appends a new time_log row (from_time = now, completed_qty = 0)
	and sets status to "Work In Progress".

	Returns: {started, skipped, failed}
	"""
	job_cards = _parse_list(job_cards, "job_cards")
	if not job_cards:
		frappe.throw(_("No Job Cards provided."))

	started, skipped, failed = [], [], []

	for name in job_cards:
		try:
			doc = frappe.get_doc("Job Card", name)

			# Only "Open" cards can be started
			if doc.status != "Open":
				skipped.append({
					"name": name,
					"reason": f"Status is '{doc.status}' (expected Open)",
				})
				continue

			employee = getattr(doc, "employee", None) or None
			doc.append("time_logs", {
				"employee": employee,
				"from_time": now_datetime(),
				"completed_qty": 0,
			})
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


# ─────────────────────────────────────────────────────────────────────────────
# Sub-operation helpers
# ─────────────────────────────────────────────────────────────────────────────

@frappe.whitelist()
def get_sub_operations_for_job_cards(job_cards):
	"""
	Return distinct sub-operation names that appear in the given Job Cards'
	sub_operations child table (status != 'Complete').

	Returns a list of {value, label} dicts suitable for a Select/Link field.
	"""
	job_cards = _parse_list(job_cards, "job_cards")
	if not job_cards:
		return []

	placeholders = ", ".join(["%s"] * len(job_cards))
	rows = frappe.db.sql(
		f"""
		SELECT DISTINCT jco.sub_operation
		FROM   `tabJob Card Operation` jco
		WHERE  jco.parent IN ({placeholders})
		  AND  jco.sub_operation IS NOT NULL
		  AND  jco.sub_operation != ''
		  AND  jco.status != 'Complete'
		ORDER BY jco.sub_operation
		""",
		tuple(job_cards),
		as_dict=True,
	)

	return [{"value": r.sub_operation, "label": r.sub_operation} for r in rows]


# ─────────────────────────────────────────────────────────────────────────────
# Bulk Complete
# ─────────────────────────────────────────────────────────────────────────────

@frappe.whitelist()
def bulk_complete_job_cards(job_cards, sub_operation=None):
	"""
	Complete multiple Job Cards in bulk.

	Only cards with status "Work In Progress" are processed.

	sub_operation (optional):
	  - If provided  → mark only that sub-operation row as "Complete" on each card.
	                    If ALL sub-operations on the card are now Complete, also set
	                    the card status to "Completed" and close any open time_log.
	  - If omitted   → close open time_logs, set completed_qty from for_qty,
	                    and set card status to "Completed" directly.

	Returns: {completed, skipped, failed}
	"""
	job_cards = _parse_list(job_cards, "job_cards")
	if not job_cards:
		frappe.throw(_("No Job Cards provided."))

	# sub_operation may arrive as a JSON string "null" or empty string
	if isinstance(sub_operation, str):
		sub_operation = sub_operation.strip() or None
	if sub_operation == "null":
		sub_operation = None

	completed, skipped, failed = [], [], []

	for name in job_cards:
		try:
			doc = frappe.get_doc("Job Card", name)

			# Only "Work In Progress" cards can be completed
			if doc.status != "Work In Progress":
				skipped.append({
					"name": name,
					"reason": f"Status is '{doc.status}' (expected Work In Progress)",
				})
				continue

			now = now_datetime()

			if sub_operation:
				# ── Complete a specific sub-operation row ──────────────────
				matched = False
				for row in doc.sub_operations or []:
					if row.sub_operation == sub_operation:
						row.status = "Complete"
						row.completed_qty = flt(getattr(doc, "for_qty", 0) or 0)
						row.completed_time = str(now)
						matched = True

				if not matched:
					skipped.append({
						"name": name,
						"reason": f"Sub-operation '{sub_operation}' not found on this card",
					})
					continue

				# If ALL sub-operations are now Complete → also complete the card
				all_done = all(
					row.status == "Complete"
					for row in (doc.sub_operations or [])
				)
				if all_done:
					_close_open_time_logs(doc, now)
					doc.status = "Completed"

			else:
				# ── Complete the whole card ────────────────────────────────
				_close_open_time_logs(doc, now)
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


def _close_open_time_logs(doc, now):
	"""Close any open time_log rows (from_time set, to_time empty) and fill qty."""
	target_qty = flt(getattr(doc, "for_qty", 0) or 0)
	for row in doc.time_logs or []:
		if row.from_time and not row.to_time:
			row.to_time = now
			if not flt(row.completed_qty):
				row.completed_qty = target_qty
