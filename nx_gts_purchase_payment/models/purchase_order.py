from odoo import models, fields,api, _


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def action_payment(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Vendor Payment'),
            'res_model': 'account.payment',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_payment_type': 'outbound',
                'default_partner_type': 'supplier',
                'default_partner_id': self.partner_id.id,
                'default_date': fields.Date.context_today(self),
                'default_purchase_id': self.id,
            },
        }

    def action_create_invoice(self):
        """Override to register related payments on the created bill."""
        result = super(PurchaseOrder, self).action_create_invoice()

        related_payments = self.env['account.payment'].search([
            ('purchase_id', '=', self.id),
            ('state', 'in', ['draft','in_process', 'paid']),
            ('payment_type', '=', 'outbound'),
        ])

        moves = self.env['account.move'].search([
            ('invoice_line_ids.purchase_line_id.order_id', '=', self.id),
            ('move_type', '=', 'in_invoice'),
        ])

        if related_payments and moves:
            for payment in related_payments:
                payment.write({'invoice_ids': [(4, inv.id) for inv in moves]})

        return result

    payment_count = fields.Integer(
        string="Payments",
        compute="_compute_payment_count"
    )

    def _compute_payment_count(self):
        for order in self:
            if order.invoice_ids:
                payments = order.invoice_ids.mapped('matched_payment_ids')
            else:
                payments = self.env['account.payment'].search([
                    ('purchase_id', '=', order.id),
                    ('state', 'in', ['draft','in_process', 'paid']),
                    ('payment_type', '=', 'outbound'),
                ])
            order.payment_count = len(payments)

    def open_payments(self):
        self.ensure_one()
        if self.invoice_ids:
            payments = self.invoice_ids.mapped('matched_payment_ids')
        else:
            payments = self.env['account.payment'].search([
                ('purchase_id', '=', self.id),
                ('state', 'in', ['draft','in_process', 'paid']),
                ('payment_type', '=', 'outbound'),
            ])
        return payments._get_records_action(name=_("Payments"))
