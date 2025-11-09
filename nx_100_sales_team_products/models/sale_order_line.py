# -*- coding: utf-8 -*-

from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    
    @api.onchange('product_id', 'product_template_id')
    def _onchange_product_check_team_access(self):
        """Check if the selected product is allowed for user's team"""
        if not self.product_template_id:
            return
        
        user = self.env.user
        product = self.product_template_id
        
        # Check team assignment filter
        if product.use_sales_team_filter and product.sales_team_ids:
            if user.sale_team_id not in product.sales_team_ids:
                return {
                    'warning': {
                        'title': 'تحذير',
                        'message': 'هذا المنتج غير متاح لفريقك.'
                    }
                }
        
        # Check category filter
        if user.sale_team_id and user.sale_team_id.product_category_ids:
            allowed_categories = user.sale_team_id.product_category_ids
            product_category = product.categ_id
            
            # Check if product category is in allowed categories or their children
            if product_category not in allowed_categories:
                # Check if it's a child category
                is_allowed = False
                for allowed_cat in allowed_categories:
                    if product_category.parent_path and allowed_cat.parent_path:
                        if product_category.parent_path.startswith(allowed_cat.parent_path):
                            is_allowed = True
                            break
                
                if not is_allowed:
                    return {
                        'warning': {
                            'title': 'تحذير',
                            'message': f'هذا المنتج من فئة "{product_category.name}" غير متاحة لفريقك.'
                        }
                    }

