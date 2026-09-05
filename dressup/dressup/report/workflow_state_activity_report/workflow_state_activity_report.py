# Copyright (c) 2026, Prime Technology of Bangladesh and contributors
# For license information, please see license.txt

import re
import frappe
from frappe import _
from frappe.utils import format_datetime, getdate, nowdate, strip_html


def execute(filters=None):
	if not filters:
		filters = {}

	columns = get_columns(filters)
	data = get_data(filters)
	chart = get_chart_data(data, filters)
	report_summary = get_report_summary(data, filters)

	return columns, data, None, chart, report_summary


def get_columns(filters):
	group_by = filters.get("group_by", "Detailed Logs")

	if group_by == "Summary by User":
		return [
			{
				"fieldname": "user",
				"label": _("User"),
				"fieldtype": "Link",
				"options": "User",
				"width": 180,
			},
			{
				"fieldname": "user_name",
				"label": _("Full Name"),
				"fieldtype": "Data",
				"width": 180,
			},
			{
				"fieldname": "total_actions",
				"label": _("Total Actions"),
				"fieldtype": "Int",
				"width": 120,
			},
			{
				"fieldname": "unique_documents",
				"label": _("Unique Documents"),
				"fieldtype": "Int",
				"width": 140,
			},
			{
				"fieldname": "last_activity",
				"label": _("Last Activity"),
				"fieldtype": "Datetime",
				"width": 160,
			},
		]

	elif group_by == "Summary by Workflow State":
		return [
			{
				"fieldname": "workflow_state",
				"label": _("Workflow State"),
				"fieldtype": "Data",
				"width": 200,
			},
			{
				"fieldname": "reference_doctype",
				"label": _("DocType"),
				"fieldtype": "Link",
				"options": "DocType",
				"width": 160,
			},
			{
				"fieldname": "total_actions",
				"label": _("Total Actions"),
				"fieldtype": "Int",
				"width": 120,
			},
			{
				"fieldname": "unique_users",
				"label": _("Unique Users"),
				"fieldtype": "Int",
				"width": 120,
			},
			{
				"fieldname": "unique_documents",
				"label": _("Unique Documents"),
				"fieldtype": "Int",
				"width": 140,
			},
			{
				"fieldname": "last_activity",
				"label": _("Last Activity"),
				"fieldtype": "Datetime",
				"width": 160,
			},
		]

	elif group_by == "Summary by DocType":
		return [
			{
				"fieldname": "reference_doctype",
				"label": _("DocType"),
				"fieldtype": "Link",
				"options": "DocType",
				"width": 180,
			},
			{
				"fieldname": "total_actions",
				"label": _("Total Actions"),
				"fieldtype": "Int",
				"width": 120,
			},
			{
				"fieldname": "unique_users",
				"label": _("Unique Users"),
				"fieldtype": "Int",
				"width": 120,
			},
			{
				"fieldname": "unique_documents",
				"label": _("Unique Documents"),
				"fieldtype": "Int",
				"width": 140,
			},
			{
				"fieldname": "last_activity",
				"label": _("Last Activity"),
				"fieldtype": "Datetime",
				"width": 160,
			},
		]

	# Default: Detailed Logs
	return [
		{
			"fieldname": "creation",
			"label": _("Date & Time"),
			"fieldtype": "Datetime",
			"width": 160,
		},
		{
			"fieldname": "user",
			"label": _("User"),
			"fieldtype": "Link",
			"options": "User",
			"width": 180,
		},
		{
			"fieldname": "user_name",
			"label": _("Full Name"),
			"fieldtype": "Data",
			"width": 160,
		},
		{
			"fieldname": "reference_doctype",
			"label": _("DocType"),
			"fieldtype": "Link",
			"options": "DocType",
			"width": 160,
		},
		{
			"fieldname": "reference_name",
			"label": _("Document"),
			"fieldtype": "Dynamic Link",
			"options": "reference_doctype",
			"width": 180,
		},
		{
			"fieldname": "previous_state",
			"label": _("From State"),
			"fieldtype": "Data",
			"width": 170,
		},
		{
			"fieldname": "workflow_state",
			"label": _("Workflow State"),
			"fieldtype": "Data",
			"width": 170,
		},
		{
			"fieldname": "content_summary",
			"label": _("Action Details"),
			"fieldtype": "Data",
			"width": 250,
		},
	]


def get_raw_activity_logs(filters):
	from_date = filters.get("from_date")
	to_date = filters.get("to_date")
	user_filter = filters.get("user")
	doctype_filter = filters.get("reference_doctype")
	state_filter = filters.get("workflow_state")

	logs = []
	user_map = {}
	doctype_permission_cache = {}

	def can_read_doctype(dt):
		if not dt:
			return False
		if dt not in doctype_permission_cache:
			doctype_permission_cache[dt] = frappe.has_permission(dt, "read")
		return doctype_permission_cache[dt]

	# Fetch user full names
	users = frappe.db.get_all("User", fields=["name", "full_name"])
	for u in users:
		user_map[u.name] = u.full_name or u.name

	# 1. Fetch Workflow Comments (from workflow_tracker)
	comment_conditions = ["comment_type = 'Workflow'"]
	values = {}

	if from_date:
		comment_conditions.append("creation >= %(from_date)s")
		values["from_date"] = f"{from_date} 00:00:00"
	if to_date:
		comment_conditions.append("creation <= %(to_date)s")
		values["to_date"] = f"{to_date} 23:59:59"
	if user_filter:
		comment_conditions.append("(comment_email = %(user)s or owner = %(user)s)")
		values["user"] = user_filter
	if doctype_filter:
		comment_conditions.append("reference_doctype = %(doctype)s")
		values["doctype"] = doctype_filter

	where_clause = " WHERE " + " AND ".join(comment_conditions) if comment_conditions else ""

	comments = frappe.db.sql(
		f"""
		SELECT name, creation, comment_email, comment_by, reference_doctype, reference_name, content
		FROM `tabComment`
		{where_clause}
		ORDER BY creation DESC
	""",
		values,
		as_dict=True,
	)

	for c in comments:
		# Check read permission for the reference doctype
		if not can_read_doctype(c.reference_doctype):
			continue

		user_id = c.comment_email or c.comment_by
		full_name = user_map.get(user_id, c.comment_by or user_id)
		prev_state, new_state = parse_comment_content(c.content)

		# Apply workflow_state filter if specified
		if state_filter:
			if not (
				(new_state and state_filter.lower() in new_state.lower())
				or (prev_state and state_filter.lower() in prev_state.lower())
			):
				continue

		logs.append(
			{
				"id": c.name,
				"creation": c.creation,
				"user": user_id,
				"user_name": full_name,
				"reference_doctype": c.reference_doctype,
				"reference_name": c.reference_name,
				"previous_state": prev_state or "-",
				"workflow_state": new_state or "-",
				"content_summary": strip_html(c.content or ""),
				"source": "Comment",
			}
		)

	# 2. Fetch Workflow Action records (Frappe Standard)
	action_conditions = ["status in ('Completed', 'Approved', 'Rejected')"]
	action_values = {}

	if from_date:
		action_conditions.append("creation >= %(from_date)s")
		action_values["from_date"] = f"{from_date} 00:00:00"
	if to_date:
		action_conditions.append("creation <= %(to_date)s")
		action_values["to_date"] = f"{to_date} 23:59:59"
	if user_filter:
		action_conditions.append("(completed_by = %(user)s or user = %(user)s)")
		action_values["user"] = user_filter
	if doctype_filter:
		action_conditions.append("reference_doctype = %(doctype)s")
		action_values["doctype"] = doctype_filter
	if state_filter:
		action_conditions.append("workflow_state LIKE %(state)s")
		action_values["state"] = f"%{state_filter}%"

	action_where = " WHERE " + " AND ".join(action_conditions) if action_conditions else ""

	try:
		workflow_actions = frappe.db.sql(
			f"""
			SELECT name, creation, completed_by, user, reference_doctype, reference_name, workflow_state, status
			FROM `tabWorkflow Action`
			{action_where}
			ORDER BY creation DESC
		""",
			action_values,
			as_dict=True,
		)

		for wa in workflow_actions:
			if not can_read_doctype(wa.reference_doctype):
				continue

			user_id = wa.completed_by or wa.user
			full_name = user_map.get(user_id, user_id)

			# Avoid duplicating if already logged via Comment at the exact same timestamp & doc
			duplicate = False
			for l in logs:
				if (
					l["reference_doctype"] == wa.reference_doctype
					and l["reference_name"] == wa.reference_name
					and abs((l["creation"] - wa.creation).total_seconds()) < 5
				):
					duplicate = True
					break

			if not duplicate:
				logs.append(
					{
						"id": wa.name,
						"creation": wa.creation,
						"user": user_id,
						"user_name": full_name,
						"reference_doctype": wa.reference_doctype,
						"reference_name": wa.reference_name,
						"previous_state": "-",
						"workflow_state": wa.workflow_state or "-",
						"content_summary": f"Action {wa.status} in state {wa.workflow_state}",
						"source": "Workflow Action",
					}
				)
	except Exception:
		pass

	# Sort all logs descending by creation timestamp
	logs.sort(key=lambda x: x["creation"], reverse=True)
	return logs


def parse_comment_content(content):
	if not content:
		return None, None

	# Pattern: changed workflow state from <strong>Old State</strong> to <strong>New State</strong>
	match = re.search(
		r"changed workflow state from <strong>(.*?)</strong> to <strong>(.*?)</strong>",
		content,
		re.IGNORECASE,
	)
	if match:
		return match.group(1).strip(), match.group(2).strip()

	# Pattern: set workflow state to <strong>New State</strong>
	match_set = re.search(
		r"set workflow state to <strong>(.*?)</strong>", content, re.IGNORECASE
	)
	if match_set:
		return None, match_set.group(1).strip()

	clean = strip_html(content or "").strip()
	return None, clean


def get_data(filters):
	raw_logs = get_raw_activity_logs(filters)
	group_by = filters.get("group_by", "Detailed Logs")

	if group_by == "Detailed Logs":
		return raw_logs

	if group_by == "Summary by User":
		user_summary = {}
		for log in raw_logs:
			u = log["user"]
			if u not in user_summary:
				user_summary[u] = {
					"user": u,
					"user_name": log["user_name"],
					"total_actions": 0,
					"documents": set(),
					"last_activity": log["creation"],
				}
			user_summary[u]["total_actions"] += 1
			user_summary[u]["documents"].add(f"{log['reference_doctype']}:{log['reference_name']}")
			if log["creation"] > user_summary[u]["last_activity"]:
				user_summary[u]["last_activity"] = log["creation"]

		result = []
		for u, data in user_summary.items():
			result.append(
				{
					"user": data["user"],
					"user_name": data["user_name"],
					"total_actions": data["total_actions"],
					"unique_documents": len(data["documents"]),
					"last_activity": data["last_activity"],
				}
			)
		result.sort(key=lambda x: x["total_actions"], reverse=True)
		return result

	if group_by == "Summary by Workflow State":
		state_summary = {}
		for log in raw_logs:
			key = (log["workflow_state"], log["reference_doctype"])
			if key not in state_summary:
				state_summary[key] = {
					"workflow_state": log["workflow_state"],
					"reference_doctype": log["reference_doctype"],
					"total_actions": 0,
					"users": set(),
					"documents": set(),
					"last_activity": log["creation"],
				}
			state_summary[key]["total_actions"] += 1
			state_summary[key]["users"].add(log["user"])
			state_summary[key]["documents"].add(log["reference_name"])
			if log["creation"] > state_summary[key]["last_activity"]:
				state_summary[key]["last_activity"] = log["creation"]

		result = []
		for key, data in state_summary.items():
			result.append(
				{
					"workflow_state": data["workflow_state"],
					"reference_doctype": data["reference_doctype"],
					"total_actions": data["total_actions"],
					"unique_users": len(data["users"]),
					"unique_documents": len(data["documents"]),
					"last_activity": data["last_activity"],
				}
			)
		result.sort(key=lambda x: x["total_actions"], reverse=True)
		return result

	if group_by == "Summary by DocType":
		doctype_summary = {}
		for log in raw_logs:
			dt = log["reference_doctype"]
			if dt not in doctype_summary:
				doctype_summary[dt] = {
					"reference_doctype": dt,
					"total_actions": 0,
					"users": set(),
					"documents": set(),
					"last_activity": log["creation"],
				}
			doctype_summary[dt]["total_actions"] += 1
			doctype_summary[dt]["users"].add(log["user"])
			doctype_summary[dt]["documents"].add(log["reference_name"])
			if log["creation"] > doctype_summary[dt]["last_activity"]:
				doctype_summary[dt]["last_activity"] = log["creation"]

		result = []
		for dt, data in doctype_summary.items():
			result.append(
				{
					"reference_doctype": data["reference_doctype"],
					"total_actions": data["total_actions"],
					"unique_users": len(data["users"]),
					"unique_documents": len(data["documents"]),
					"last_activity": data["last_activity"],
				}
			)
		result.sort(key=lambda x: x["total_actions"], reverse=True)
		return result

	return raw_logs


def get_chart_data(data, filters):
	if not data:
		return None

	group_by = filters.get("group_by", "Detailed Logs")
	labels = []
	values = []

	if group_by == "Detailed Logs":
		# Group actions by Workflow State for top 7 states
		state_counts = {}
		for row in data:
			st = row.get("workflow_state") or "Unknown"
			state_counts[st] = state_counts.get(st, 0) + 1

		sorted_states = sorted(state_counts.items(), key=lambda x: x[1], reverse=True)[:7]
		labels = [s[0] for s in sorted_states]
		values = [s[1] for s in sorted_states]

	elif group_by == "Summary by User":
		for row in data[:7]:
			labels.append(row.get("user_name") or row.get("user"))
			values.append(row.get("total_actions", 0))

	elif group_by == "Summary by Workflow State":
		for row in data[:7]:
			labels.append(f"{row.get('workflow_state')} ({row.get('reference_doctype')})")
			values.append(row.get("total_actions", 0))

	elif group_by == "Summary by DocType":
		for row in data[:7]:
			labels.append(row.get("reference_doctype"))
			values.append(row.get("total_actions", 0))

	if not labels or not values:
		return None

	return {
		"data": {
			"labels": labels,
			"datasets": [{"name": _("Actions Count"), "values": values}],
		},
		"type": "bar",
		"colors": ["#5e64ff", "#22c55e", "#f59e0b", "#ef4444", "#a855f7", "#06b6d4", "#64748b"],
	}


def get_report_summary(data, filters):
	if not data:
		return []

	group_by = filters.get("group_by", "Detailed Logs")

	if group_by == "Detailed Logs":
		total_actions = len(data)
		users_set = {d.get("user") for d in data if d.get("user")}
		docs_set = {f"{d.get('reference_doctype')}:{d.get('reference_name')}" for d in data}

		return [
			{
				"value": total_actions,
				"label": _("Total State Changes"),
				"datatype": "Int",
				"indicator": "Blue",
			},
			{
				"value": len(users_set),
				"label": _("Active Users"),
				"datatype": "Int",
				"indicator": "Green",
			},
			{
				"value": len(docs_set),
				"label": _("Documents Updated"),
				"datatype": "Int",
				"indicator": "Orange",
			},
		]
	else:
		total_actions = sum(d.get("total_actions", 0) for d in data)
		return [
			{
				"value": total_actions,
				"label": _("Total Actions"),
				"datatype": "Int",
				"indicator": "Blue",
			},
			{
				"value": len(data),
				"label": _("Grouped Items"),
				"datatype": "Int",
				"indicator": "Green",
			},
		]
