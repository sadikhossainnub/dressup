import frappe


def cancel_linked_pps_and_qi(doc, method=None):
	"""Before cancelling BOM, cancel linked PPS and its submitted QI docs."""
	pps_name = doc.get("pre_production_sample")
	if not pps_name:
		return

	# 1) Cancel submitted Quality Inspection linked to this PPS
	qi_names = frappe.get_all(
		"Quality Inspection",
		filters={
			"reference_type": "Pre Production Sample",
			"reference_name": pps_name,
			"docstatus": 1,
		},
		pluck="name",
	)

	for qi_name in qi_names:
		qi = frappe.get_doc("Quality Inspection", qi_name)
		qi.cancel()

	# 2) Cancel submitted PPS
	pps = frappe.get_doc("Pre Production Sample", pps_name)
	if pps.docstatus == 1:
		pps.cancel()

