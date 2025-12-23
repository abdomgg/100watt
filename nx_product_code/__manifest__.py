{
    "name": "Product Reference in SO & PO Lines",
    "version": "18.0.1.0.0",
    'company': 'NextEra MEA',
    "summary": "Add product reference field in sale order and purchase order lines",
    "description": """
        This module adds a product reference field in sale order lines and purchase order lines,
        allowing users to select products based on their unique codes.
    """,
    "depends": ["sale_management", "purchase"],
    "data": [
        "security/ir.model.access.csv",
        "data/product_code_sequence.xml",
        "views/sale_order_views.xml",
        "views/purchase_order_views.xml",
        "views/product_template_views.xml"
    ],
    "installable": True,
}
