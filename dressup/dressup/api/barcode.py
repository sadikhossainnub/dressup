import frappe
import io
import barcode
from barcode.writer import ImageWriter


@frappe.whitelist(allow_guest=True)
def get_barcode(value, barcode_type="code128", height=35, width=1.5):
	code = barcode.get(barcode_type.lower(), value, writer=ImageWriter())

	buffer = io.BytesIO()
	code.write(buffer, options={"module_height": float(height) / 10, "quiet_zone": 1})

	frappe.response["type"] = "download"
	frappe.response["filecontent"] = buffer.getvalue()
	frappe.response["filename"] = f"{value}.png"
	frappe.response["content_type"] = "image/png"
	frappe.response["display_content_as"] = "inline"
