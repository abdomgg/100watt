{
    'name': 'GTS Purchase Payment',
    'version': '18.0.1.0.0',
    'category': 'Purchase',
    'summary': 'Add Payment button to Purchase Order',
    'description': """
        GTS Purchase Payment
        ====================
        This module adds a Payment button to the purchase order form view,
        allowing users to quickly create and register payments directly from purchase orders.
        
        Features:
        ---------
        * Payment button in purchase order header
        * Quick access to payment registration
        * Streamlined payment workflow for purchase orders
        * Enhanced payment views for better usability
        
        Module developed for GTS by Nextera.
    """,
    'author': 'Nextera-Mahmoud Yousry',
    'depends': ['purchase'],
    'data': [
        'security/payment_security.xml',
        'views/purchase_order_views.xml',
        'views/account_payment_views.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
}
