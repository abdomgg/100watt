from odoo import models, fields

class ProductCode(models.Model):
    _name = 'product.code'
    _description = 'Product Code'
    _rec_name = 'code'

    code = fields.Char(
        string='Product Code',
        required=True,
        index=True
    )

    product_tmpl_id = fields.Many2one(
        'product.template',
        string='Product',
        ondelete='cascade'
    )

    _sql_constraints = [
        ('code_unique', 'unique(code)', 'Product Code must be unique!')
    ]
