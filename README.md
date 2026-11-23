# GulfPOS — Multi-Currency Cloud ERP & Micro-POS System

A full-stack, bilingual (**English LTR / Arabic RTL**) Point-of-Sale and Enterprise Resource Planning web application engineered for GCC & cross-border retail workflows.

## Key Enterprise Features
- **Real-Time Multi-Currency Engine:** Live REST API exchange rate conversion across **KWD (Kuwaiti Dinar)**, **INR (Indian Rupee)**, and **USD (US Dollar)** with localized decimal precision (3 decimals for KWD).
- **Bilingual RTL/LTR Localization:** One-click layout direction flip (`dir="ltr"` ↔ `dir="rtl"`) with dual English/Arabic product catalogs.
- **Printable GCC Tax Invoices & QR Verification:** Generates sequential `INV-2026-XXXX` receipts with 5% VAT calculation, thermal/A4 print stylesheets, and dynamic e-Invoice QR codes.
- **Hardware Barcode Scanner Support:** Keyboard-wedge SKU auto-add (`Enter` trigger + `F2` focus shortcut) with audio scan feedback.
- **Role-Based Access Control (RBAC):** Instant switching between **Cashier Terminal** mode and PIN-protected **Manager ERP** mode (`Demo PIN: 1234`).
- **Relational Audit Trail & Financial Analytics:** Tracks wholesale cost vs. retail price for net profit calculation, immutable invoice line-items, interactive **Chart.js** dashboards, and one-click Excel/CSV export.

## Tech Stack
- **Backend:** Python 3, Flask, SQLite3, Requests, Gunicorn
- **Frontend:** HTML5, Tailwind CSS, Vanilla JavaScript, Chart.js, QRCode.js

## Local Setup Instructions
```bash
git clone [https://github.com/YOUR_USERNAME/gulfpos-smart-erp.git](https://github.com/YOUR_USERNAME/gulfpos-smart-erp.git)
cd gulfpos-smart-erp
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app.py