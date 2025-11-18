from email.policy import default
from odoo import fields, models, api, _
from odoo.osv import expression


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    cid = fields.Selection([
        ('local', 'Local'),
        ('international', 'International'),
    ], string='CID Type',default='local')

    Acid = fields.Char(string='ACID number')


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    code = fields.Char(string='Product Code',default="New")

    @api.model
    def create(self, vals):
        if not vals.get('code') or vals.get('code') == "New":
            seq = self.env['ir.sequence'].next_by_code('product_cod')
            vals['code'] = seq or "New"
        return super(ProductTemplate, self).create(vals)

    def name_get(self):
        result = []
        super_obj = super(ProductTemplate, self)
        if hasattr(super_obj, 'name_get'):
            super_names = dict(super_obj.name_get())
        else:
            super_names = {}
        for template in self:
            name = super_names.get(template.id, template.name)
            prefix = template.code or template.default_code
            if prefix:
                name = "[%s] %s" % (prefix, name)
            result.append((template.id, name))
        return result

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        args = args or []
        res = super(ProductTemplate, self).name_search(name=name, args=args, operator=operator, limit=limit)
        if not name:
            return res
        res_ids = {r[0] for r in res}
        # Compute remaining quota
        remaining = None if not limit else max(limit - len(res_ids), 0)
        if remaining == 0:
            return res
        domain = ['|', ('code', operator, name), ('default_code', operator, name)]
        search_domain = expression.AND([args, domain])
        templates = self.search(search_domain, limit=remaining)
        res.extend([(rec_id, rec_name) for rec_id, rec_name in templates.name_get() if rec_id not in res_ids])
        return res


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def name_get(self):
        result = []
        super_obj = super(ProductProduct, self)
        if hasattr(super_obj, 'name_get'):
            super_names = dict(super_obj.name_get())
        else:
            super_names = {}
        for product in self:
            name = super_names.get(product.id, product.display_name or product.name)
            prefix = product.product_tmpl_id.code or product.default_code
            if prefix:
                name = "[%s] %s" % (prefix, name)
            result.append((product.id, name))
        return result

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        args = args or []
        res = super(ProductProduct, self).name_search(name=name, args=args, operator=operator, limit=limit)
        if not name:
            return res
        res_ids = {r[0] for r in res}
        remaining = None if not limit else max(limit - len(res_ids), 0)
        if remaining == 0:
            return res
        domain = ['|', ('product_tmpl_id.code', operator, name), ('default_code', operator, name)]
        search_domain = expression.AND([args, domain])
        products = self.search(search_domain, limit=remaining)
        res.extend([(rec_id, rec_name) for rec_id, rec_name in products.name_get() if rec_id not in res_ids])
        return res


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    product_code = fields.Char(
        string='Product Code',
        related='product_id.product_tmpl_id.code',
        readonly=True,
    )


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    product_code = fields.Char(
        string='Product Code',
        related='product_id.product_tmpl_id.code',
        readonly=True,
    )










