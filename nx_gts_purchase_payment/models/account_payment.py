from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    purchase_id = fields.Many2one(
        'purchase.order',
        string="Purchase Order",
        help="Purchase Order linked to this payment",
    )

    @api.model
    def create(self, vals):
        payment = super().create(vals)

        if payment.purchase_id:
            moves = self.env['account.move'].search([
                ('invoice_line_ids.purchase_line_id.order_id', '=', payment.purchase_id.id),
                ('move_type', '=', 'in_invoice'),
            ])
            if moves:
                payment.write({'invoice_ids': [(4, inv.id) for inv in moves]})
            payment._auto_confirm_purchase_payment()

        return payment

    def action_post(self):
        res = super().action_post()
        purchase_payments = self.filtered('purchase_id')

        for payment in purchase_payments:
            purchase_group = self.env.ref("purchase.group_purchase_user")
            users = purchase_group.users
            partner_ids = users.mapped("partner_id").ids

            if not partner_ids:
                continue

            confirm_user = self.env.user
            confirm_time = fields.Datetime.context_timestamp(
                self, fields.Datetime.now()
            ).strftime("%d-%m-%Y %H:%M:%S")

            vendor_name = payment.partner_id.name or "Vendor"

            payment_link = (
                f"<a href='/web#id={payment.id}&model=account.payment&view_type=form'>{payment.name}</a>"
            )
            order_link = (
                f"<a href='/web#id={payment.purchase_id.id}&model=purchase.order&view_type=form'>{payment.purchase_id.name}</a>"
            )

            body = (
                f"Vendor Payment {payment_link} related to Purchase Order {order_link}"
                f"<ul>"
                f"<li><b>Vendor:</b> {vendor_name}</li>"
                f"<li><b>Confirmed By:</b> {confirm_user.name}</li>"
                f"<li><b>Date:</b> {confirm_time}</li>"
                f"</ul>"
            )

            # Post on Purchase Order
            payment.purchase_id.message_post(
                body=body,
                body_is_html=True,
                partner_ids=partner_ids,
                message_type="comment",
                subtype_xmlid="mail.mt_comment",
            )

            # Post on Payment
            payment.message_post(
                body=body,
                body_is_html=True,
                partner_ids=partner_ids,
                message_type="comment",
                subtype_xmlid="mail.mt_comment",
            )

            # Post on Vendor Bill(s) linked with this payment
            if payment.invoice_ids:
                for bill in payment.invoice_ids:
                    bill.message_post(
                        body=body,
                        body_is_html=True,
                        partner_ids=partner_ids,
                        message_type="comment",
                        subtype_xmlid="mail.mt_comment",
                    )

        purchase_payments._auto_confirm_purchase_payment()
        return res

    def action_open_manual_reconciliation_widget(self):
        """Fallback manual reconciliation for community builds."""
        self.ensure_one()

        move_line = False
        for line in self.move_id.line_ids:
            if line.account_id.reconcile:
                move_line = line.id
                break

        if not self.partner_id:
            raise UserError(_("Payments without a customer can't be matched"))

        action_context = {
            'company_ids': [self.company_id.id],
            'partner_ids': [self.partner_id.commercial_partner_id.id],
        }

        if self.partner_type == 'customer':
            action_context['mode'] = 'customers'
        elif self.partner_type == 'supplier':
            action_context['mode'] = 'suppliers'

        if move_line:
            action_context['move_line_id'] = move_line

        action_values = self.env['ir.actions.act_window']._for_xml_id('account.action_account_moves_all_grouped_matching')
        action_values['domain'] = [
            ('partner_id', '=', self.partner_id.commercial_partner_id.id),
            ('reconciled', '=', False),
            ('parent_state', '!=', 'cancel'),
        ]
        action_values['context'] = {
            'search_default_partner_id': self.partner_id.commercial_partner_id.id,
            'search_default_posted': 1,
            'default_partner_id': self.partner_id.commercial_partner_id.id,
        }
        action_values['target'] = 'current'
        return action_values

    def _auto_confirm_purchase_payment(self):
        """Automatically confirm & validate purchase payments to reach Paid state."""
        for payment in self.filtered('purchase_id'):
            if payment.state == 'draft':
                payment.action_post()
            if payment.state == 'in_process':
                action_validate = getattr(payment, "action_validate", None)
                if action_validate:
                    action_validate()
                else:
                    payment.write({'state': 'paid'})
