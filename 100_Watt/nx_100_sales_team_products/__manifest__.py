# -*- coding: utf-8 -*-
{
    'name': 'Sales Team Products Filter - 100 Watt',
    'version': '1.0.0',
    'category': 'Sales',
    'summary': 'Filter products by sales team - each team sees only assigned products',
    'description': """
        Sales Team Products Filter
        ===========================
        This module allows you to assign specific products to sales teams.
        
        Features:
        - Add sales team assignment to products
        - Checkbox to enable/disable product sales team filter
        - Each sales team sees only their assigned products
        - Filter by product categories
        
        Module developed for 100 Watt with Arabic language support.
    """,
    'author': '100 Watt',
    'website': '',
    'depends': ['base', 'product', 'sale', 'sales_team'],
    'data': [
        'security/ir_rule.xml',
        'views/crm_team_views.xml',
        'views/product_template_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}

