# -*- coding: utf-8 -*-
import io
import base64

from odoo import fields, models
from odoo.exceptions import UserError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    invoice_line_statement_ids = fields.One2many(
        comodel_name='account.move.line',
        inverse_name='partner_id',
        string='Invoice Lines',
        domain=[
            ('move_id.state', '!=', 'cancel'),
            # if you want only customer invoices & refunds, uncomment:
            # ('move_id.move_type', 'in', ['out_invoice', 'out_refund']),
        ],
        readonly=True,
    )

    invoice_ids = fields.One2many(
        'account.move',
        'partner_id',
        string='Invoices',
        domain=[
            ('move_type', 'in', ['out_invoice', 'out_refund', 'in_invoice', 'in_refund']),
            ('state', '!=', 'cancel'),
        ],
    )

    # ===== your actions (unchanged) =====
    def action_print_customer_statement_pdf(self):
        self.ensure_one()
        return self.env.ref(
            'nx_100_customer_statement.action_report_customer_statement_pdf'
        ).report_action(self)

    def action_print_customer_statement_excel(self):
        self.ensure_one()
        invoices = self.invoice_ids.sorted('invoice_date', reverse=True)
        output = io.BytesIO()
        try:
            import xlsxwriter
            workbook = xlsxwriter.Workbook(output, {'in_memory': True})
            worksheet = workbook.add_worksheet('Customer Statement')

            header_format = workbook.add_format({
                'bold': True,
                'bg_color': '#366092',
                'font_color': 'white',
            })
            date_format = workbook.add_format({'num_format': 'yyyy-mm-dd'})
            currency_format = workbook.add_format({'num_format': '#,##0.00'})

            headers = [
                'Invoice Date',
                'Invoice No.',
                'Due Date',
                'Total Amount',
                'Amount Due',
                'Balance',
            ]
            for col, header in enumerate(headers):
                worksheet.write(0, col, header, header_format)

            row = 1
            balance = 0.0
            for invoice in invoices:
                balance += invoice.amount_total_signed
                worksheet.write(row, 0, invoice.invoice_date or '', date_format)
                worksheet.write(row, 1, invoice.name or '')
                worksheet.write(row, 2, invoice.invoice_date_due or '', date_format)
                worksheet.write(row, 3, invoice.amount_total_signed, currency_format)
                worksheet.write(row, 4, invoice.amount_residual_signed, currency_format)
                worksheet.write(row, 5, balance, currency_format)
                row += 1

            worksheet.set_column(0, 0, 15)
            worksheet.set_column(1, 1, 20)
            worksheet.set_column(2, 2, 15)
            worksheet.set_column(3, 5, 15)

            workbook.close()
            output.seek(0)

            excel_file = base64.b64encode(output.read())
            output.close()

            attachment = self.env['ir.attachment'].create({
                'name': 'Customer Statement - %s.xlsx' % self.name,
                'type': 'binary',
                'datas': excel_file,
                'res_model': 'res.partner',
                'res_id': self.id,
            })

            return {
                'type': 'ir.actions.act_url',
                'url': '/web/content/%s?download=true' % attachment.id,
                'target': 'self',
            }
        except ImportError:
            raise UserError(
                'xlsxwriter library is not installed. Please install it to use Excel export.'
            )
        except Exception as e:
            raise UserError('Error generating Excel file: %s' % str(e))

    def action_send_customer_statement_pdf(self):
        self.ensure_one()
        if not self.email:
            raise UserError('This partner does not have an email address configured.')

        compose_form = self.env.ref('mail.email_compose_message_wizard_form', False)
        ctx = dict(
            default_model='res.partner',
            default_res_id=self.id,
            default_composition_mode='comment',
            default_partner_ids=[(6, 0, [self.id])],
        )
        return {
            'name': 'Send Customer Statement PDF',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form.id, 'form')],
            'view_id': compose_form.id,
            'target': 'new',
            'context': ctx,
        }

    def action_send_customer_statement_excel(self):
        self.ensure_one()
        if not self.email:
            raise UserError('This partner does not have an email address configured.')

        compose_form = self.env.ref('mail.email_compose_message_wizard_form', False)
        ctx = dict(
            default_model='res.partner',
            default_res_id=self.id,
            default_composition_mode='comment',
            default_partner_ids=[(6, 0, [self.id])],
        )
        return {
            'name': 'Send Customer Statement Excel',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form.id, 'form')],
            'view_id': compose_form.id,
            'target': 'new',
            'context': ctx,
        }
