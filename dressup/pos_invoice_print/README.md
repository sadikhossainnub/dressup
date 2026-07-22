# POS Thermal Receipt Print Format

A thermal receipt print format for Dress Up Bangladesh, designed specifically for 80mm thermal printers with Bangladesh tax invoice (MUSAK-6.3) compliance.

## Features

- **Thermal Printer Optimized**: Designed for 80mm thermal receipt printers
- **Bangladesh Tax Compliant**: Includes MUSAK-6.3 tax invoice format
- **Compact Layout**: Optimized for receipt paper with minimal margins
- **Brand Identity**: Dress Up branding with company details
- **Loyalty Program**: Displays loyalty points information
- **Payment Details**: Shows payment mode, paid amount, and change
- **Professional Footer**: Includes exchange policy and terms

## Installation

1. **Verify the print format files exist**:
   ```
   /home/sayed/frappe-bench/apps/dressup/dressup/pos_invoice_print/
   ├── print_format/
   │   └── thermal_receipt/
   │       ├── thermal_receipt.html
   │       └── thermal_receipt.json
   └── __init__.py
   ```

2. **Install the print format in Frappe**:
   ```bash
   # Navigate to your Frappe bench directory
   cd /home/sayed/frappe-bench

   # Migrate the site to install the print format
   bench --site [your-site-name] migrate

   # Clear cache
   bench clear-cache

   # Restart bench
   bench restart
   ```

## Usage

1. **In Sales Invoice**:
   - Create or open a Sales Invoice
   - In the Print Format dropdown, select **"POS Thermal Receipt"**
   - Click the Print button

2. **Print Settings**:
   - Ensure your printer is set to 80mm width
   - Use raw printing mode for thermal printers
   - No page margins (already configured in the template)

## Print Format Details

### Template Structure

```jinja2
{%- macro add_header() -%}
  ... (empty macro to prevent default header)
{%- endmacro -%}

<style>
  @page { size: 80mm auto; margin: 0mm; }
  .pos-receipt { width: 72mm; ... }
</style>

<div class="pos-receipt">
  <!-- 1. Brand Header -->
  <!-- 2. Tax Invoice Header -->
  <!-- 3. Invoice Meta (Invoice No, Date, Cashier) -->
  <!-- 4. Items Table -->
  <!-- 5. Totals Section -->
  <!-- 6. Payment Information -->
  <!-- 7. Customer Details -->
  <!-- 8. Loyalty Points -->
  <!-- 9. Footer Terms -->
</div>
```

### Key Sections

1. **Brand Header**: Dress Up branding with Bangladesh address and VAT registration
2. **Tax Invoice**: MUSAK-6.3 compliant header for Bangladesh tax requirements
3. **Invoice Meta**: Invoice number, date/time, and cashier information
4. **Items Table**: Compact items list with serial, product, price, quantity, amount
5. **Totals**: Subtotal, discount, taxes, net payable, rounding, net due
6. **Payment**: Mode of payment, paid amount, change amount
7. **Customer**: Customer name and mobile number
8. **Loyalty Points**: Current invoice points, total accumulated points, membership tier
9. **Footer**: Exchange policy and terms

## Configuration (JSON)

```json
{
  "name": "POS Thermal Receipt",
  "doc_type": "Sales Invoice",
  "print_format_type": "Jinja",
  "raw_printing": 1,
  "margin_bottom": 0.0,
  "margin_left": 0.0,
  "margin_right": 0.0,
  "margin_top": 0.0,
  "page_number": "Hide"
}
```

## Customization

To customize the print format:

1. **Modify the HTML template**:
   - Edit `/dressup/pos_invoice_print/print_format/thermal_receipt/thermal_receipt.html`
   - Make changes to the CSS or HTML structure

2. **Update company details**:
   - Change "DRESS UP" brand name
   - Update address in the template
   - Modify footer terms as needed

3. **Adjust print settings**:
   - Edit `/dressup/pos_invoice_print/print_format/thermal_receipt/thermal_receipt.json`
   - Modify margins, page size, or other print settings

## Testing

After installation, test the print format by:

1. Creating a test Sales Invoice
2. Adding some items
3. Selecting "POS Thermal Receipt" as the print format
4. Clicking Print (or Print Preview)

The receipt should display in a compact 72mm width format suitable for thermal printers.

## Troubleshooting

1. **Print format not appearing in dropdown**:
   - Run `bench --site [site-name] migrate` again
   - Clear cache with `bench clear-cache`
   - Restart bench with `bench restart`

2. **Print alignment issues**:
   - Check printer settings for 80mm width
   - Ensure raw printing is enabled
   - Verify no margins are added by printer driver

3. **Template errors**:
   - Check Frappe error log
   - Verify Jinja syntax in the HTML template
   - Ensure all required fields exist in the Sales Invoice doctype

## Support

For issues or questions:
- Check Frappe documentation for print formats
- Review Jinja template documentation
- Contact Dress Up development team