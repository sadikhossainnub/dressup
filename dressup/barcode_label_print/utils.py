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
        code_type_map = {
            "upc-a": "upca",
            "jan": "ean13",
        }
        
        normalized_type = code_type.lower().replace(" ", "")
        barcode_format = code_type_map.get(normalized_type, normalized_type)
        
        if barcode_format == "qrcode":
            return get_qr_base64(code_value)

        # Create barcode class
        try:
            BarcodeClass = barcode.get_barcode_class(barcode_format)
        except barcode.errors.BarcodeNotFoundError:
             frappe.throw(f"Barcode type '{code_type}' is not supported.")
        
        # Generate barcode using ImageWriter (PNG) for scanner readability
        my_barcode = BarcodeClass(str(code_value), writer=ImageWriter())
        
        # Writer options optimized for barcode scanner readability
        # Key principles:
        #   - module_width: minimum bar width. Wider = easier to scan.
        #     0.4mm is safe for most handheld scanners.
        #   - module_height: height of bars. Taller = more forgiving scan angle.
        #     15mm gives good scan reliability.
        #   - quiet_zone: blank space on left/right of barcode.
        #     Must be at least 10x module_width per ISO standard.
        #   - dpi: 300 for print. Don't lower this.
        #   - write_text: False because we render text separately in HTML
        #     (gives better control over font/positioning).
        writer_options = {
            "write_text": False,
            "module_width": 0.40,      # mm — wider bars for reliable scanning
            "module_height": 15.0,     # mm — tall bars improve scan rate
            "quiet_zone": 1.0,         # mm — adequate quiet zone for scanners
            "text_distance": 2.0,
            "dpi": 300,                # High DPI for crisp print output
            "font_size": 0,
        }
        
        rv = BytesIO()
        my_barcode.write(rv, options=writer_options)
        rv.seek(0)
        
        # Convert PNG to base64
        img_str = base64.b64encode(rv.getvalue()).decode("utf-8")
        return f"data:image/png;base64,{img_str}"
        
    except Exception as e:
        frappe.log_error(f"Error generating barcode ({code_type}, {code_value}): {str(e)}", "Barcode Generation Error")
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
