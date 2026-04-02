# DressUp

DressUp is a powerful manufacturing and garment industry-focused ERPNext app. It streamlines operations from cost estimation and pre-production sampling to barcode label printing with highly customizable templates.

## 🚀 Key Features

### 🏷️ Barcode & QR Label Printing
A specialized module for generating and printing high-quality barcode and QR code labels for items, batches, and serial numbers.

- **Dynamic Layouts:** Support for multiple labels per row with configurable gaps and margins.
- **Three Printing Modes:**
  - **Barcode Only:** Supports standard formats (Code128, Code39, EAN, etc.).
  - **QR Code Only:** Large, centered QR codes for high-density data.
  - **Dual Mode:** Both barcode and QR code on the same label for maximum compatibility.
- **Scanner Optimized:** Barcodes are generated with precise bar widths (no CSS stretching) to ensure 100% scan reliability.
- **Template Builder:** Define label sizes (e.g., 45mm x 35mm), font sizes, and exactly what information to include (Price, Batch, Serial, Company, etc.).

### ➕ Bulk Item Management
Efficiency tools for managing large quantities of items in the Label Print form.
- **Bulk Add Dialog:** Search, filter, and pick multiple items with custom quantities in one go.
- **Item Group Import:** Pull all items from a specific group (e.g., "Cotton Fabrics") instantly.
- **Fast Clearing:** One-click clear-all tool for table management.

### 👕 Garment Manufacturing (DressUp Module)
Comprehensive suite for the apparel industry:
- **Pre-Production Sample (PPS):** Track sample development, size charts (in inches), and checklists.
- **Cost Estimation:** Detailed material and accessory breakdown for accurate garment costing.
- **Sketch Specification:** Manage technical packs, main sketches, and image-based specification sheets.
- **Fabric & Trim Details:** Highly granular tracking of fabric compositions, dyes, and accessories.

### 🏢 Asset & Rental Management
- **Rented Assets:** Track assets leased out to branches or departments.
- **Renewal System:** Automated rental agreement renewal logs and dashboard indicators.

## 🛠️ Modules Included
- **DressUp:** Core manufacturing, PPS, Costing, and Quality hooks.
- **Barcode Label Print:** Print formats, barcode/QR generation, and label design templates.

---

## 📦 Installation

Install this app on your Frappe bench:

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app https://github.com/sadikhossainnub/dressup
bench install-app dressup
bench migrate
```

## 👨‍💻 Contributing

This app uses `pre-commit` for code formatting and linting.

```bash
cd apps/dressup
pre-commit install
```

Tools configured:
- **ruff**: Python linting and formatting.
- **eslint**: Javascript linting.
- **prettier**: CSS and HTML formatting.
- **pyupgrade**: Modernizes Python syntax.

## 📜 License

This project is licensed under the **GPL-3.0**.
