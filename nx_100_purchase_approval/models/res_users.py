from odoo import fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    purchase_approver_ids = fields.One2many(
        'purchase.order.approver',
        'user_id',
        string='Purchase Approvers',
        help='Users who can approve purchase orders created by this user'
    )

