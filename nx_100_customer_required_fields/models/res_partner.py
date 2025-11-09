# -*- coding: utf-8 -*-

from odoo import api, models
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.constrains('name')
    def _check_required_customer_fields(self):
        """Validate that required fields are filled for customers"""
        for partner in self:
            # Only apply validation for customers (not companies or contacts)
            if partner.customer_rank > 0 or (not partner.parent_id and not partner.is_company):
                if not partner.name:
                    raise ValidationError('اسم العميل مطلوب.')

