{
    'name': 'Admin Full Access - No Restrictions',
    'version': '18.0.1.0.1',
    'category': 'Administration',
    'summary': 'Give administrators full access to all companies and records without any restrictions',
    'description': """
        Admin Full Access
        ==================
        This module removes all multi-company restrictions for administrators.
        Administrators can create, read, update, and delete records for ANY company
        regardless of their current company or allowed companies list.
        
        This bypasses all multi-company rules for users in the "Settings" group.
    """,
    'author': 'Ahmed Tarek',
    'depends': ['base', 'product', 'sales_team'],
    'data': [
        'security/ir.model.access.csv',
        'security/admin_security.xml',
    ],
    'post_init_hook': '_post_init_hook',
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
