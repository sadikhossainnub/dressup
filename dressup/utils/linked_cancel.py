import frappe

def cancel_linked_documents(doc, method=None):
	if getattr(doc.flags, "in_auto_cancel", False):
		return
	doc.flags.in_auto_cancel = True

	if doc.doctype == "Pre Production Sample":
		# Cancel Work Orders linked to this PPS
		wos = frappe.get_all("Work Order", filters={"pre_production_sample": doc.name, "docstatus": 1}, pluck="name")
		for wo in wos:
			wo_doc = frappe.get_doc("Work Order", wo)
			wo_doc.flags.in_auto_cancel = True
			wo_doc.cancel()
		
		# Cancel BOMs linked to this PPS
		boms = frappe.get_all("BOM", filters={"pre_production_sample": doc.name, "docstatus": 1}, pluck="name")
		for bom in boms:
			bom_doc = frappe.get_doc("BOM", bom)
			bom_doc.flags.in_auto_cancel = True
			bom_doc.cancel()
			
		# Cancel QIs linked to this PPS
		qis = frappe.get_all("Quality Inspection", filters={"reference_type": "Pre Production Sample", "reference_name": doc.name, "docstatus": 1}, pluck="name")
		for qi in qis:
			qi_doc = frappe.get_doc("Quality Inspection", qi)
			qi_doc.flags.in_auto_cancel = True
			qi_doc.cancel()

	elif doc.doctype == "BOM":
		# Cancel Work Orders linked to this BOM
		wos = frappe.get_all("Work Order", filters={"bom_no": doc.name, "docstatus": 1}, pluck="name")
		for wo in wos:
			wo_doc = frappe.get_doc("Work Order", wo)
			wo_doc.flags.in_auto_cancel = True
			wo_doc.cancel()
			
		pps_name = doc.get("pre_production_sample")
		if pps_name:
			# Cancel PPS
			pps = frappe.get_doc("Pre Production Sample", pps_name)
			if pps.docstatus == 1:
				pps.flags.in_auto_cancel = True
				pps.cancel()
				
			# Cancel QIs linked to this PPS
			qis = frappe.get_all("Quality Inspection", filters={"reference_type": "Pre Production Sample", "reference_name": pps_name, "docstatus": 1}, pluck="name")
			for qi in qis:
				qi_doc = frappe.get_doc("Quality Inspection", qi)
				qi_doc.flags.in_auto_cancel = True
				qi_doc.cancel()

	elif doc.doctype == "Work Order":
		bom_name = doc.get("bom_no")
		if bom_name:
			bom = frappe.get_doc("BOM", bom_name)
			if bom.docstatus == 1:
				bom.flags.in_auto_cancel = True
				bom.cancel()
				
		pps_name = doc.get("pre_production_sample")
		if pps_name:
			pps = frappe.get_doc("Pre Production Sample", pps_name)
			if pps.docstatus == 1:
				pps.flags.in_auto_cancel = True
				pps.cancel()
				
			# Cancel QIs linked to this PPS
			qis = frappe.get_all("Quality Inspection", filters={"reference_type": "Pre Production Sample", "reference_name": pps_name, "docstatus": 1}, pluck="name")
			for qi in qis:
				qi_doc = frappe.get_doc("Quality Inspection", qi)
				qi_doc.flags.in_auto_cancel = True
				qi_doc.cancel()
