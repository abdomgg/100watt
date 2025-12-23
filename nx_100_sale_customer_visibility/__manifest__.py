{
    "name": "Sales Customer Visibility",
    "summary": "Limit salespeople to their own customers and auto-show Team Leader on partner.",
    "version": "18.0.1.1.0",
    "category": "Sales",
    "author": "Ahmed Tarek",
    "license": "LGPL-3",
    "description": """
        Sales Customer Visibility - 100 Watt
        =====================================
        This module restricts salespeople to view and manage only their own customers,
        sales orders, and CRM opportunities.
        
        Features:
        ---------
        * Salespeople can only see customers assigned to them
        * Salespeople can only see their own sales orders
        * Salespeople can only see their own CRM opportunities
        * Team Leaders automatically displayed on partner form
        * Security rules ensure data isolation between salespeople
        * Maintains proper access for managers and administrators
        
        Module developed for 100 Watt.
    """,

    "depends": [
        "sale_management",
        "purchase",        # needed because field is shown in Sales & Purchase notebook
        "crm",             # needed for CRM opportunity visibility rules
    ],

    "data": [
        # SECURITY
        "security/ir.model.access.csv",
        "security/res_partner_rule.xml",
        "security/res_users_rule.xml",
        "security/sale_order_rule.xml",
        "security/crm_lead_rule.xml",

        # VIEWS
        "views/res_partner_view.xml",
    ],

    "installable": True,
    "application": False,
}
