from email.policy import default
from odoo import fields, models, api


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    cid = fields.Selection([
        ('local', 'Local'),
        ('international', 'International'),
    ], string='CID Type',default='local')

    Acid = fields.Char(string='ACID number')


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    code = fields.Char(string='Product Code')

    @api.model
    def create(self, vals):
        # If code not provided, generate from sequence
        if not vals.get('code'):
            vals['code'] = self.env['ir.sequence'].next_by_code('product_cod') or '/'
        return super(ProductTemplate, self).create(vals)










