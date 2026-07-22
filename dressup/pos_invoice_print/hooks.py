from . import __version__ as app_version

app_name = "pos_invoice_print"
app_title = "POS Invoice Print"
app_publisher = "Dress Up"
app_description = "POS Thermal Receipt Print Format for Dress Up"
app_email = "admin@dressup.com"
app_license = "MIT"

# Fixtures
fixtures = [
    {
        "dt": "Print Format",
        "filters": [
            ["name", "in", ["POS Thermal Receipt"]]
        ]
    }
]

# Print Format registration
print_format_script = "pos_invoice_print.print_format.thermal_receipt.thermal_receipt"