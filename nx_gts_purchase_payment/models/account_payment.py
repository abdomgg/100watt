from odoo import models, fields, api, _


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

        return payment

    def action_post(self):
        res = super().action_post()
        for payment in self:
            if not payment.purchase_id:
                continue

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

        return res
