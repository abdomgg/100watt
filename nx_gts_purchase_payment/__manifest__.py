{
    'name': 'GTS Purchase Payment',
    'version': '18.0.1.0.0',
    'category': 'Purchase',
    'summary': 'Add Payment button to Purchase Order',
    'description': 'This module adds a Payment button to the purchase order header.',
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
