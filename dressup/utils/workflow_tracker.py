import frappe
from frappe.model.workflow import get_workflow_name, get_workflow_state_field


def track_workflow_action(doc, method=None):
	"""
	Generic handler for all doctypes — tracks who performed workflow state changes.
	Adds a Comment to the document timeline showing the user's full name
	and the workflow action (e.g., Approved, Rejected, etc.).

	This is triggered via doc_events["*"]["on_update"] in hooks.py.
	"""
	# Skip if doctype has no active workflow
	workflow_name = get_workflow_name(doc.doctype)
	if not workflow_name:
		return

	workflow_state_field = get_workflow_state_field(workflow_name)
	current_state = doc.get(workflow_state_field)

	if not current_state:
		return

	# Get previous state
	previous = doc.get_doc_before_save()
	old_state = previous.get(workflow_state_field) if previous else None

	# Only act when the workflow state has actually changed
	if old_state == current_state:
		return

	# Get current user's full name
	current_user = frappe.session.user
	full_name = frappe.db.get_value("User", current_user, "full_name") or current_user

	# Build the comment message
	if old_state:
		comment_text = f"<strong>{full_name}</strong> changed workflow state from <strong>{old_state}</strong> to <strong>{current_state}</strong>"
	else:
		comment_text = f"<strong>{full_name}</strong> set workflow state to <strong>{current_state}</strong>"

	# Add a Comment to the document timeline
	frappe.get_doc({
		"doctype": "Comment",
		"comment_type": "Workflow",
		"reference_doctype": doc.doctype,
		"reference_name": doc.name,
		"content": comment_text,
		"comment_email": current_user,
		"comment_by": full_name
	}).insert(ignore_permissions=True)
