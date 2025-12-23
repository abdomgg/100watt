{
    "name": "NX 100 Partner Ledger Products",
    "version": "18.0.1.0.0",
    "category": "Accounting",
    "summary": "Add product / price / quantity columns to Partner Ledger",
    "description": """
        Partner Ledger Products Extension
        ==================================
        
        This module extends the Partner Ledger report by adding three additional columns:
        
        * **Products**: Displays product names from invoice lines
        * **Price**: Shows unit prices for each product
        * **Quantity**: Lists quantities for each product
        
        Features:
        ---------
        * Automatically extracts product information from invoices and refunds
        * Supports multi-line display with proper formatting
        * Includes RTL (Arabic) layout optimizations for PDF exports
        * Reduces margins and scales content to fit all columns in Arabic reports
    """,
    "author": "Ahmed Tarek",
    "license": "OEEL-1",
    "depends": [
        "account",
        "account_reports",
    ],
    "data": [
        "data/partner_ledger_columns.xml",
        "views/pdf_export_templates.xml",
    ],
    "assets": {
        "account_reports.assets_pdf_export": [
            "nx_100_partner_ledger_products/static/src/scss/partner_ledger_rtl.scss",
        ],
    },
    "installable": True,
    "application": False,
}