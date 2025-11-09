# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    use_sales_team_filter = fields.Boolean(
        string='تفعيل فلتر فريق المبيعات',
        default=False,
        help='إذا تم التفعيل، سيكون هذا المنتج مرئياً فقط لفرق المبيعات المحددة'
    )
    
    sales_team_ids = fields.Many2many(
        'crm.team',
        'product_template_sales_team_rel',
        'product_id',
        'team_id',
        string='فرق المبيعات',
        help='فرق المبيعات التي يمكنها رؤية هذا المنتج'
    )
    
    @api.model
    def _search(self, domain, offset=0, limit=None, order=None):
        """Override search to filter products by user's team categories"""
        # Apply category filtering based on user's sales team
        user = self.env.user
        
        # Only apply filtering for non-managers
        if not user.has_group('sales_team.group_sale_manager'):
            if user.sale_team_id and user.sale_team_id.product_category_ids:
                # Get all allowed category IDs
                allowed_category_ids = user.sale_team_id.product_category_ids.ids
                
                # BOTH conditions are MANDATORY:
                # 1. Checkbox must be enabled
                # 2. Category MUST be in team's assigned categories
                # 3. Product MUST be assigned to the team
                category_domain = [
                    ('use_sales_team_filter', '=', True),  # Filter MUST be enabled
                    ('categ_id', 'in', allowed_category_ids),  # Category MUST be in team's categories
                    ('sales_team_ids', 'in', user.sale_team_id.ids)  # Product MUST be assigned to team
                ]
                
                # Combine with existing domain using AND
                if domain:
                    domain = ['&'] + domain + category_domain
                else:
                    domain = category_domain
        
        return super(ProductTemplate, self)._search(
            domain, offset=offset, limit=limit, order=order
        )

