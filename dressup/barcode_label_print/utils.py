import base64
from io import BytesIO
import barcode
from barcode.writer import ImageWriter
import qrcode
import frappe

def get_barcode_base64(code_type, code_value):
    """
    Generate a barcode image and return it as a base64 string.
    :param code_type: The type of barcode (e.g., 'code128', 'ean13', 'code39').
    :param code_value: The value to encode.
    :return: Base64 encoded string of the image.
    """
    if not code_value:
        return None
        
    try:
        # Map ERPNext/User friendly names to python-barcode names
        # python-barcode supports: code128, code39, ean, ean13, ean8, gs1, gtinean, isbn, isbn10, isbn13, issn, jan, pzn, upc, upca
        
        code_type_map = {
            "upc-a": "upca",
            "jan": "ean13", # JAN is EAN13 with specific prefix
        }
        
        normalized_type = code_type.lower().replace(" ", "")
        barcode_format = code_type_map.get(normalized_type, normalized_type)
        
        if barcode_format == "qrcode":
            return get_qr_base64(code_value)

        rv = BytesIO()
        
        # Create barcode class
        try:
            BarcodeClass = barcode.get_barcode_class(barcode_format)
        except barcode.errors.BarcodeNotFoundError:
             frappe.throw(f"Barcode type '{code_type}' is not supported.")
        
        # Generate barcode
        # writer_options = {"write_text": False} # Optional: hide text if handled by template
        my_barcode = BarcodeClass(code_value, writer=ImageWriter())
        
        # Write to stream
        my_barcode.write(rv)
        
        # Convert to base64
        img_str = base64.b64encode(rv.getvalue()).decode("utf-8")
        return f"data:image/png;base64,{img_str}"
        
    except Exception as e:
        frappe.log_error(f"Error generating barcode ({code_type}, {code_value}): {str(e)}", "Barcode Generation Error")
        # Return None so the label can still print without the barcode if it fails
        return None

def get_qr_base64(data):
    """
    Generate a QR code image and return it as a base64 string.
    :param data: The data to encode.
    :return: Base64 encoded string of the image.
    """
    if not data:
        return None
        
    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        
        rv = BytesIO()
        img.save(rv, format="PNG")
        
        img_str = base64.b64encode(rv.getvalue()).decode("utf-8")
        return f"data:image/png;base64,{img_str}"
    except Exception as e:
        frappe.log_error(f"Error generating QR code ({data}): {str(e)}", "QR Code Generation Error")
        return None
