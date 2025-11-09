# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    customer_vat = fields.Char(
        string='الرقم الضريبي', 
        related='partner_id.vat',
        store=True,
        readonly=False,
        required=True,
        help='الرقم الضريبي للعميل'
    )

    @api.constrains('customer_vat')
    def _check_vat_required(self):
        """Validate that Tax ID is required"""
        for order in self:
            if not order.customer_vat:
                raise ValidationError('الرقم الضريبي مطلوب لإنشاء عرض أسعار.')

