from odoo import models, fields


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    cid = fields.Selection([
        ('local', 'Local'),
        ('international', 'International'),
    ], string='CID Type', default='local')

    Acid = fields.Char(string='ACID number')
