from odoo import models, api, _
from odoo.exceptions import AccessError


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.model_create_multi
    def create(self, vals_list):
        user = self.env.user

        if not user.has_group('product_restrict.group_product_creator'):
            raise AccessError(_('You do not have permission to create products. Please contact your administrator.'))

        products = super(ProductProduct, self).create(vals_list)

        return products

    def unlink(self):
        user = self.env.user

        if not user.has_group('product_restrict.group_product_creator'):
            raise AccessError(_('You do not have permission to delete products. Please contact your administrator.'))

        return super(ProductProduct, self).unlink()


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.model_create_multi
    def create(self, vals_list):
        user = self.env.user

        if not user.has_group('product_restrict.group_product_creator'):
            raise AccessError(
                _('You do not have permission to create product templates. Please contact your administrator.'))

        templates = super(ProductTemplate, self).create(vals_list)

        return templates

    def unlink(self):
        user = self.env.user

        if not user.has_group('product_restrict.group_product_creator'):
            raise AccessError(
                _('You do not have permission to delete product templates. Please contact your administrator.'))

        return super(ProductTemplate, self).unlink()