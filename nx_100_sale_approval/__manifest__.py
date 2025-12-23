{
    'name': 'Sale Order Approval - 100 Watt',
    'version': '1.0.2',
    'category': 'Sales',
    'summary': 'Require approval before confirming sale orders/quotations',
    'description': """
        Sale Order Approval - 100 Watt
        ===============================
        This module adds an approval workflow for sale orders/quotations with automatic
        stock validation before sending approval requests.
        
        Features:
        ---------
        * Configure approvers in user settings
        * Require approval before confirming quotations
        * Stock availability validation before approval request
        * Prevents approval workflow if products are out of stock
        * Send approval activities to specified approvers
        * Track approval status with pending/approved/rejected states
        * Multiple approvers support with required/optional settings
        * Automatic order confirmation after approval
        * Team leaders can bypass approval requirements
        
        Module developed for 100 Watt.
    """,
    'author': 'Ahmed Tarek',
    'depends': ['base', 'sale', 'mail', 'stock'],
    'data': [
        'security/ir.model.access.csv',
        'views/res_users_views.xml',
        'views/sale_order_views.xml',
    ],
    # 'post_init_hook': 'post_init_hook',
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}

