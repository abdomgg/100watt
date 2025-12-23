from odoo import models, api
from odoo.osv import expression


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.model
    def _name_search(self, name='', args=None, operator='ilike', limit=100, order=None):
        args = args or []
        
        if name:
            domain = [
                '|', '|',
                ('name', operator, name),
                ('default_code', operator, name),
                ('product_tmpl_id.product_code_id.code', operator, name)
            ]
            return self._search(expression.AND([domain, args]), limit=limit, order=order)
        
        return super()._name_search(name=name, args=args, operator=operator, limit=limit, order=order)

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        args = args or []

        result = super().name_search(name, args, operator, limit)

        if not name:
            return result

        existing_ids = {res[0] for res in result}

        positive_operators = ['=', 'ilike', '=ilike', 'like', '=like']
        domain = args or []

        limit_rest = limit and (limit - len(result))
        if limit_rest is not None and limit_rest <= 0:
            return result

        products = self.search_fetch(
            expression.AND([
                domain,
                [('product_tmpl_id.product_code_id.code', operator, name)],
                [('id', 'not in', list(existing_ids))]
            ]),
            ['display_name'],
            limit=limit_rest
        )

        result.extend([
            (p.id, p.display_name)
            for p in products.sudo()
        ])

        return result

    # @api.depends('name', 'default_code', 'product_tmpl_id.product_code_id')
    # @api.depends_context('display_default_code', 'seller_id', 'company_id', 'partner_id')
    # def _compute_display_name(self):
    #     super()._compute_display_name()
    #
    #     if not self.env.context.get('display_default_code', True):
    #         return
    #
    #     for product in self:
    #         if not product.display_name:
    #             continue
    #
    #         tmpl_code = product.product_tmpl_id.product_code_id
    #         default_code = product.default_code
    #
    #         if tmpl_code:
    #             if default_code and product.display_name.startswith(f'[{default_code}]'):
    #                 product.display_name = (
    #                     f'[{tmpl_code}]{product.display_name}'
    #                 )
    #             elif default_code:
    #                 product.display_name = (
    #                     f'[{tmpl_code}][{default_code}] '
    #                     f'{product.display_name.replace(f"[{default_code}] ", "")}'
    #                 )
    #             else:
    #                 product.display_name = f'[{tmpl_code}] {product.display_name}'