from odoo import fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    sale_approver_ids = fields.One2many(
        'sale.order.approver',
        'user_id',
        string='Approvers',
        help='Users who can approve sale orders created by this user'
    )

