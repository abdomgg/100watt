{
    'name': 'Customer Required Fields - 100 Watt',
    'version': '1.0.0',
    'category': 'Sales',
    'summary': 'Make customer name, phone, and company required; Tax ID required in sales orders; Company required for products',
    'description': """
        Customer Required Fields
        =========================
        This module makes the following fields required when creating a customer:
        - Name
        - Phone Number
        - Company
        
        Note: Phone number is NOT required when creating users from Settings.
        Address is optional for customers.
        
        Also requires:
        - Tax ID when creating sales orders (auto-populated from customer if available)
        - Company field for products
        
        Module developed for 100 Watt with Arabic language support.
    """,
    'author': 'Ahmed Tarek',
    'depends': ['base', 'contacts', 'sale', 'crm', 'product'],
    'data': [
        'views/res_partner_views.xml',
        'views/sale_order_views.xml',
        'views/crm_lead_views.xml',
        'views/product_template_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}

