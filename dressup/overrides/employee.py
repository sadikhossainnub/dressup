import frappe

def set_employee_number(doc, method):
    if not doc.employee_number:
        doc.employee_number = doc.name
