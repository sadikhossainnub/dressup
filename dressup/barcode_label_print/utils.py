import base64
from io import BytesIO
import barcode
from barcode.writer import SVGWriter, ImageWriter
import qrcode
import qrcode.image.svg
import frappe

def get_barcode_base64(code_type, code_value):
    """
    Generate a barcode image and return it as a base64 string.
    Uses vector SVG for razor-sharp, zero-dithering print output on thermal printers.
    Falls back to high-resolution PNG if SVG generation fails.
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
        
        # Try generating vector SVG first for crisp print output on thermal printers
        try:
            my_barcode = BarcodeClass(str(code_value), writer=SVGWriter())
            writer_options = {
                "write_text": False,
                "module_width": 0.35,      # mm — wider bars for reliable scanning
                "module_height": 15.0,     # mm — tall bars improve scan rate
                "quiet_zone": 1.0,         # mm — adequate quiet zone for scanners
            }
            rv = BytesIO()
            my_barcode.write(rv, options=writer_options)
            rv.seek(0)
            img_str = base64.b64encode(rv.getvalue()).decode("utf-8")
            return f"data:image/svg+xml;base64,{img_str}"
        except Exception:
            # Fallback to high-DPI ImageWriter (PNG)
            my_barcode = BarcodeClass(str(code_value), writer=ImageWriter())
            writer_options = {
                "write_text": False,
                "module_width": 0.35,
                "module_height": 15.0,
                "quiet_zone": 1.0,
                "text_distance": 2.0,
                "dpi": 300,
                "font_size": 0,
            }
            rv = BytesIO()
            my_barcode.write(rv, options=writer_options)
            rv.seek(0)
            img_str = base64.b64encode(rv.getvalue()).decode("utf-8")
            return f"data:image/png;base64,{img_str}"
        
    except Exception as e:
        frappe.log_error(f"Error generating barcode ({code_type}, {code_value}): {str(e)}", "Barcode Generation Error")
        return None

def get_qr_base64(data):
    """
    Generate a QR code image and return it as a base64 string.
    Uses vector SVG for razor-sharp, zero-dithering print output on thermal printers.
    Falls back to high-resolution PNG if SVG generation fails.
    :param data: The data to encode.
    :return: Base64 encoded string of the image.
    """
    if not data:
        return None
        
    try:
        # Try vector SVG first for crisp edges and zero anti-aliasing blur
        try:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_M,
                box_size=10,
                border=1,
            )
            qr.add_data(str(data))
            qr.make(fit=True)
            img = qr.make_image(image_factory=qrcode.image.svg.SvgPathImage)
            rv = BytesIO()
            img.save(rv)
            rv.seek(0)
            img_str = base64.b64encode(rv.getvalue()).decode("utf-8")
            return f"data:image/svg+xml;base64,{img_str}"
        except Exception:
            # Fallback to PNG
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_M,
                box_size=15,
                border=1,
            )
            qr.add_data(str(data))
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            rv = BytesIO()
            img.save(rv, format="PNG")
            rv.seek(0)
            img_str = base64.b64encode(rv.getvalue()).decode("utf-8")
            return f"data:image/png;base64,{img_str}"
    except Exception as e:
        frappe.log_error(f"Error generating QR code ({data}): {str(e)}", "QR Code Generation Error")
        return None
