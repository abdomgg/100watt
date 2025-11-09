# -*- coding: utf-8 -*-
{
    'name': 'Customer Required Fields - 100 Watt',
    'version': '1.0.0',
    'category': 'Sales',
    'summary': 'Make customer name required and Tax ID required in sales orders',
    'description': """
        Customer Required Fields
        =========================
        This module makes the following fields required when creating a customer:
        - Name
        
        Also requires Tax ID when creating sales orders (auto-populated from customer if available).
        Module developed for 100 Watt with Arabic language support.
    """,
    'author': '100 Watt',
    'website': '',
    'depends': ['base', 'contacts', 'sale', 'crm'],
    'data': [
        'views/res_partner_views.xml',
        'views/sale_order_views.xml',
        'views/crm_lead_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}

