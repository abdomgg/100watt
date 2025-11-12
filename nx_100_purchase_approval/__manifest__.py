{
    'name': 'Purchase Order Approval - 100 Watt',
    'version': '1.0.0',
    'category': 'Purchases',
    'summary': 'Require approval before confirming purchase orders',
    'description': """
        Purchase Order Approval
        =======================
        This module adds an approval workflow for purchase orders.
        
        Features:
        - Configure approvers in user settings
        - Require approval before confirming purchase orders
        - Send approval activities to specified approvers
        - Track approval status
        - Multiple approvers support with required/optional settings
        
        Module developed for 100 Watt.
    """,
    'author': '100 Watt',
    'website': '',
    'depends': ['base', 'purchase', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'views/res_users_views.xml',
        'views/purchase_order_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}

