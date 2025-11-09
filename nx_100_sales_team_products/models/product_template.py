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
    
    # @api.model
    # def _search(self, domain, offset=0, limit=None, order=None):
    #     """Override search to filter products by user's team categories"""
    #     # Apply category filtering based on user's sales team
    #     user = self.env.user
    #
    #     # Only apply filtering for non-managers
    #     if not user.has_group('sales_team.group_sale_manager'):
    #         if user.sale_team_id and user.sale_team_id.product_category_ids:
    #             # Get all allowed category IDs including children
    #             allowed_categories = user.sale_team_id.product_category_ids
    #             category_ids = allowed_categories.ids
    #
    #             # Add children categories
    #             for category in allowed_categories:
    #                 child_categories = self.env['product.category'].search([
    #                     ('parent_path', 'like', category.parent_path + '%')
    #                 ])
    #                 category_ids.extend(child_categories.ids)
    #
    #             # Add category filter to domain
    #             category_domain = [
    #                 '|',
    #                 ('categ_id', 'in', category_ids),
    #                 ('categ_id', '=', False)
    #             ]
    #             domain = domain + category_domain if domain else category_domain
    #
    #     return super(ProductTemplate, self)._search(
    #         domain, offset=offset, limit=limit, order=order
    #     )

