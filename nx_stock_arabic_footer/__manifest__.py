{
    'name': 'Stock Arabic Footer',
    'version': '1.0',
    'category': 'Inventory',
    'summary': 'Add Arabic footer to stock delivery and return reports',
    'description': """
        This module adds an Arabic acknowledgment footer to stock reports:
        - Delivery slip reports (incoming only)
        - Picking operations reports (incoming only)
        - Return slip reports (all returns)
        
        The footer includes signature and date fields for confirmation.
    """,
    'depends': ['stock'],
    'data': [
        'report/stock_report_arabic_footer.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
