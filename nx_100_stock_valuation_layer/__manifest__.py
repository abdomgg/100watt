{
    "name": "Stock Valuation Layer - 100 Watt",
    "summary": "Add on-hand quantity and total inventory value to stock valuation layer list view",
    "version": "18.0.1.0.0",
    "category": "Inventory",
    "author": "Ahmed Tarek",
    "license": "LGPL-3",
    "description": """
        Stock Valuation Layer Customization - 100 Watt
        ===============================================
        This module adds custom fields to the stock valuation layer list view:
        
        Features:
        ---------
        * On-hand quantity for each product
        * Total inventory value (القيمة الكلية المخزنية)
        
        Module developed for 100 Watt.
    """,

    "depends": [
        "stock_account",
    ],

    "data": [
        "views/stock_valuation_layer_view.xml",
    ],

    "installable": True,
    "application": False,
}
