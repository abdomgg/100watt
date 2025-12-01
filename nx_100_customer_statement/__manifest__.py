
{
    'name': 'Customer Statement - 100 Watt',
    'version': '1.0.2',
    'category': 'Accounting',
    'summary': 'Add Customer Statement tab to partner form with print and email options',
    'description': """
        Customer Statement
        ==================
        This module adds a Customer Statement tab to the partner form.
        
        Features:
        - Customer Statement tab in partner form
        - Print PDF and Excel statements
        - Send PDF and Excel statements by email
        - Display invoice details with balance information
        
        Module developed for 100 Watt.
    """,
    'author': 'Ahmed Tarek',
    'depends': ['base', 'account', 'contacts', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'views/res_partner_views.xml',
        'report/customer_statement_report.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
