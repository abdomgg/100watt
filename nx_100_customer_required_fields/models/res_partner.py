# -*- coding: utf-8 -*-

from odoo import api, models
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.constrains('name', 'phone')
    def _check_required_customer_fields(self):
        """Validate that required fields are filled for customers only"""
        for partner in self:
            # Skip validation for users (partners linked to user accounts)
            if partner.user_ids:
                continue
            
            # Skip validation if this is being created/edited in user context
            context = self.env.context
            if (context.get('active_model') == 'res.users' or
                context.get('create_user')):
                continue
            
            # Only apply validation for actual customers (with customer_rank > 0)
            # This automatically excludes users since users don't have customer_rank set
            if partner.customer_rank > 0:
                if not partner.name:
                    raise ValidationError('اسم العميل مطلوب.')
                if not partner.phone:
                    raise ValidationError('رقم الهاتف مطلوب.')

