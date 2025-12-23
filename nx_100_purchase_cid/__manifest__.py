{
    "name": "Purchase Order CID - 100 Watt",
    "summary": "Add CID Type and ACID number fields to purchase orders",
    "version": "18.0.1.0.0",
    "category": "Purchase",
    "author": "Ahmed Tarek",
    "license": "LGPL-3",
    "description": """
        Purchase Order CID Customization - 100 Watt
        ============================================
        This module adds CID type and ACID number fields to purchase orders.
        
        Features:
        ---------
        * CID Type field (Local/International) with radio widget
        * ACID number field (hidden when CID type is Local)
        
        Module developed for 100 Watt.
    """,

    "depends": [
        "purchase",
    ],

    "data": [
        "views/purchase_order_view.xml",
    ],

    "installable": True,
    "application": False,
}
