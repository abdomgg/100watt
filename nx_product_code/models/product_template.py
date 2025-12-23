from odoo import models, fields, api, _
from odoo.osv import expression

class ProductTemplate(models.Model):
    _inherit = 'product.template'


    product_code_id = fields.Many2one(
        'product.code',
        string='Product Code',
        readonly=True,
        copy=False,
    )

    # -------------------------------------------------------------------------
    # Override create
    # -------------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        templates = super().create(vals_list)

        seq = self.env['ir.sequence']
        ProductCode = self.env['product.code']

        for tmpl in templates:
            code = seq.next_by_code('product.code')
            pc = ProductCode.create({
                'code': code,
                'product_tmpl_id': tmpl.id
            })
            tmpl.product_code_id = pc

        return templates


    @api.model
    def _name_search(self, name='', args=None, operator='ilike', limit=100, order=None):
        args = args or []
        
        if name:
            domain = [
                '|', '|',
                ('name', operator, name),
                ('default_code', operator, name),
                ('product_code_id.code', operator, name)
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
        if operator not in positive_operators:
            return result

        limit_rest = limit and (limit - len(result))
        if limit_rest is not None and limit_rest <= 0:
            return result

        templates = self.search_fetch(
            expression.AND([
                args,
                [('product_code_id.code', operator, name)],
                [('id', 'not in', list(existing_ids))],
            ]),
            ['display_name'],
            limit=limit_rest
        )

        result.extend([
            (tmpl.id, tmpl.display_name)
            for tmpl in templates.sudo()
        ])

        return result