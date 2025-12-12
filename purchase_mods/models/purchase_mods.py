from email.policy import default
import re

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

    def _get_next_product_code(self):
        """Return the next code based on the last created product's code.

        Uses the numeric suffix of the latest code (manual or automatic) and
        increments it, preserving any prefix and zero padding. Falls back to
        the configured sequence if no numeric suffix is found.
        """
        last_product = self.search([('code', 'not in', (False, '', 'New'))], order='id desc', limit=1)
        last_code = last_product.code or ''
        match = re.search(r'(\d+)(?!.*\d)', last_code)
        if match:
            prefix = last_code[:match.start(1)]
            number_part = match.group(1)
            next_number = int(number_part) + 1
            return f"{prefix}{next_number:0{len(number_part)}d}"
        # Fallback to sequence when no usable numeric suffix exists
        return self.env['ir.sequence'].next_by_code('product_cod') or 'New'

    @api.model
    def create(self, vals):
        if not vals.get('code') or vals.get('code') == "New":
            vals['code'] = self._get_next_product_code()
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

    # Many2one to leverage dropdown suggestions and partial search on code
    product_code = fields.Many2one(
        'product.product',
        string='Product Code',
        domain=lambda self: [('sale_ok', '=', True)],
    )

    @api.onchange('product_code')
    def _onchange_product_code(self):
        """When code is chosen, sync the actual product."""
        if self.product_code:
            self.product_id = self.product_code
        else:
            self.product_id = False

    @api.onchange('product_id')
    def _onchange_product_id_set_code(self):
        """Keep product_code aligned when product is picked."""
        self.product_code = self.product_id if self.product_id else False


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    product_code = fields.Many2one(
        'product.product',
        string='Product Code',
        domain=lambda self: [('purchase_ok', '=', True)],
    )

    @api.onchange('product_code')
    def _onchange_product_code(self):
        """When code is chosen, sync the actual product."""
        if self.product_code:
            self.product_id = self.product_code
        else:
            self.product_id = False

    @api.onchange('product_id')
    def _onchange_product_id_set_code(self):
        """Keep product_code aligned when product is picked."""
        self.product_code = self.product_id if self.product_id else False