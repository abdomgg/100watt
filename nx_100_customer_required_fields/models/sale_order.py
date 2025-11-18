from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    customer_vat = fields.Char(
        string='الرقم الضريبي',
        related='partner_id.vat',
        store=True,
        readonly=False,
        required=False,
        help='الرقم الضريبي للعميل'
    )

