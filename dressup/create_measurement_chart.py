import frappe

def create_doctypes():
    # Create Child Table
    if not frappe.db.exists("DocType", "Measurement Chart Item"):
        doc = frappe.get_doc({
            "doctype": "DocType",
            "name": "Measurement Chart Item",
            "module": "Dressup",
            "custom": 0,
            "istable": 1,
            "editable_grid": 1,
            "fields": [
                {"fieldname": "code", "fieldtype": "Data", "label": "Code", "in_list_view": 1, "columns": 1},
                {"fieldname": "point_of_measures", "fieldtype": "Data", "label": "Point of Measures", "reqd": 1, "in_list_view": 1, "columns": 2},
                {"fieldname": "s_b_i", "fieldtype": "Data", "label": "S B/I", "in_list_view": 1},
                {"fieldname": "s_a_i", "fieldtype": "Data", "label": "S A/I", "in_list_view": 1},
                {"fieldname": "m_b_i", "fieldtype": "Data", "label": "M B/I", "in_list_view": 1},
                {"fieldname": "m_a_i", "fieldtype": "Data", "label": "M A/I", "in_list_view": 1},
                {"fieldname": "l_b_i", "fieldtype": "Data", "label": "L B/I", "in_list_view": 1},
                {"fieldname": "l_a_i", "fieldtype": "Data", "label": "L A/I", "in_list_view": 1},
                {"fieldname": "xl_b_i", "fieldtype": "Data", "label": "XL B/I", "in_list_view": 1},
                {"fieldname": "xl_a_i", "fieldtype": "Data", "label": "XL A/I", "in_list_view": 1},
                {"fieldname": "xxl_b_i", "fieldtype": "Data", "label": "XXL B/I", "in_list_view": 1},
                {"fieldname": "xxl_a_i", "fieldtype": "Data", "label": "XXL A/I", "in_list_view": 1},
                {"fieldname": "3xl_b_i", "fieldtype": "Data", "label": "3XL B/I", "in_list_view": 1},
                {"fieldname": "3xl_a_i", "fieldtype": "Data", "label": "3XL A/I", "in_list_view": 1},
                {"fieldname": "4xl_b_i", "fieldtype": "Data", "label": "4XL B/I", "in_list_view": 1},
                {"fieldname": "4xl_a_i", "fieldtype": "Data", "label": "4XL A/I", "in_list_view": 1}
            ]
        })
        doc.insert(ignore_permissions=True)
        frappe.db.commit()
        print("Measurement Chart Item created.")
    else:
        print("Measurement Chart Item already exists.")

    # Create Parent DocType
    if not frappe.db.exists("DocType", "Measurement Chart"):
        doc = frappe.get_doc({
            "doctype": "DocType",
            "name": "Measurement Chart",
            "module": "Dressup",
            "custom": 0,
            "is_submittable": 0,
            "fields": [
                {"fieldname": "brand", "fieldtype": "Data", "label": "Brand", "in_list_view": 1},
                {"fieldname": "style_no", "fieldtype": "Data", "label": "Style No", "in_list_view": 1, "reqd": 1},
                {"fieldname": "category_lead", "fieldtype": "Data", "label": "Category Lead"},
                {"fieldname": "season", "fieldtype": "Data", "label": "Season"},
                {"fieldname": "cb_1", "fieldtype": "Column Break"},
                {"fieldname": "style_description", "fieldtype": "Data", "label": "Style Description"},
                {"fieldname": "designer", "fieldtype": "Data", "label": "Designer"},
                {"fieldname": "category", "fieldtype": "Data", "label": "Category"},
                {"fieldname": "cb_2", "fieldtype": "Column Break"},
                {"fieldname": "no_of_colorways", "fieldtype": "Data", "label": "No. of Colorways"},
                {"fieldname": "sourcing_lead", "fieldtype": "Data", "label": "Sourcing Lead"},
                {"fieldname": "collection", "fieldtype": "Data", "label": "Collection"},
                {"fieldname": "cb_3", "fieldtype": "Column Break"},
                {"fieldname": "sample_size", "fieldtype": "Data", "label": "Sample Size"},
                {"fieldname": "concern_merchan", "fieldtype": "Data", "label": "Concern Merchan"},
                {"fieldname": "sb_1", "fieldtype": "Section Break", "label": "Measurement Chart"},
                {"fieldname": "measurement_chart_items", "fieldtype": "Table", "label": "Measurement Chart Items", "options": "Measurement Chart Item"}
            ]
        })
        doc.insert(ignore_permissions=True)
        frappe.db.commit()
        print("Measurement Chart created.")
    else:
        print("Measurement Chart already exists.")

if __name__ == "__main__":
    create_doctypes()
