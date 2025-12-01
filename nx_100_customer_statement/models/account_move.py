# -*- coding: utf-8 -*-
from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    statement_product_name = fields.Char(
        string='Product',
        compute='_compute_statement_product_info',
        store=False,
    )
    statement_price_unit = fields.Float(
        string='Price',
        compute='_compute_statement_product_info',
        store=False,
    )
    statement_quantity = fields.Float(
        string='Quantity',
        compute='_compute_statement_product_info',
        store=False,
    )

    @api.depends('invoice_line_ids', 'invoice_line_ids.product_id',
                 'invoice_line_ids.name', 'invoice_line_ids.price_unit',
                 'invoice_line_ids.quantity')
    def _compute_statement_product_info(self):
        """
        Super simple version:
        - Take the *first* invoice line (no filters, no sorting)
        - Use its product / name / price / qty
        """
        for move in self:
            # get first invoice line, if any
            first_line = move.invoice_line_ids[:1]
            if first_line:
                line = first_line[0]
                move.statement_product_name = (
                    line.product_id.display_name or line.name or ''
                )
                move.statement_price_unit = line.price_unit or 0.0
                move.statement_quantity = line.quantity or 0.0
            else:
                move.statement_product_name = ''
                move.statement_price_unit = 0.0
                move.statement_quantity = 0.0

