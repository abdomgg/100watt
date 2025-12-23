from odoo import api, models
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.constrains('company_id')
    def _check_company_id(self):
        """Validate that company is filled for products"""
        for product in self:
            if not product.company_id:
                raise ValidationError('الشركة مطلوبة للمنتج.')
