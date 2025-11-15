{
    'name': 'Sale Order Approval - 100 Watt',
    'version': '1.0.0',
    'category': 'Sales',
    'summary': 'Require approval before confirming sale orders/quotations',
    'description': """
        Sale Order Approval
        ===================
        This module adds an approval workflow for sale orders/quotations.
        
        Features:
        - Configure approvers in user settings
        - Require approval before confirming quotations
        - Send approval activities to specified approvers
        - Track approval status
        - Multiple approvers support with required/optional settings
        
        Module developed for 100 Watt.
    """,
    'author': 'Ahmed Tarek',
    'website': '',
    'depends': ['base', 'sale', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'views/res_users_views.xml',
        'views/sale_order_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}

