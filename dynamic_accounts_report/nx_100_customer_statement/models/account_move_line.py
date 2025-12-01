# -*- coding: utf-8 -*-
from odoo import fields, models


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    statement_invoice_date = fields.Date(
        string='Invoice Date',
        related='move_id.invoice_date',
        store=False,
    )
    statement_invoice_name = fields.Char(
        string='Invoice No.',
        related='move_id.name',
        store=False,
    )
    statement_invoice_date_due = fields.Date(
        string='Due Date',
        related='move_id.invoice_date_due',
        store=False,
    )
    statement_amount_total_signed = fields.Monetary(
        string='Total Amount',
        related='move_id.amount_total_signed',
        store=False,
        currency_field='currency_id',
    )
    statement_amount_residual_signed = fields.Monetary(
        string='Amount Due',
        related='move_id.amount_residual_signed',
        store=False,
        currency_field='currency_id',
    )
