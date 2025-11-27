import base64
from io import BytesIO
import barcode
from barcode.writer import ImageWriter
import qrcode

def get_barcode_base64(code_type, code_value):
    """
    Generate a barcode image and return it as a base64 string.
    :param code_type: The type of barcode (e.g., 'code128', 'ean13', 'code39').
    :param code_value: The value to encode.
    :return: Base64 encoded string of the image.
    """
    try:
        # Map ERPNext/User friendly names to python-barcode names if necessary
        # python-barcode supports: code128, code39, ean, ean13, ean8, gs1, gtinean, isbn, isbn10, isbn13, issn, jan, pzn, upc, upca
        
        code_type = code_type.lower().replace("-", "").replace(" ", "")
        
        if code_type == "qrcode":
            return get_qr_base64(code_value)

        # Special handling for some types if needed, but python-barcode is quite flexible
        
        rv = BytesIO()
        # writer_options = {"write_text": False} # Optional: hide text if handled by template
        
        # Create barcode class
        BarcodeClass = barcode.get_barcode_class(code_type)
        
        # Generate barcode
        my_barcode = BarcodeClass(code_value, writer=ImageWriter())
        
        # Write to stream
        my_barcode.write(rv)
        
        # Convert to base64
        img_str = base64.b64encode(rv.getvalue()).decode("utf-8")
        return f"data:image/png;base64,{img_str}"
        
    except Exception as e:
        # Fallback or error handling
        print(f"Error generating barcode: {e}")
        return None

def get_qr_base64(data):
    """
    Generate a QR code image and return it as a base64 string.
    :param data: The data to encode.
    :return: Base64 encoded string of the image.
    """
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
        print(f"Error generating QR code: {e}")
        return None
