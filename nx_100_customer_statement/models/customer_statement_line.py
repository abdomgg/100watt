# -*- coding: utf-8 -*-

from odoo import api, fields, models


class CustomerStatementLine(models.Model):
    _name = 'customer.statement.line'
    _description = 'Customer Statement Line'
    _order = 'invoice_date desc, invoice_name, sequence'

    partner_id = fields.Many2one('res.partner', string='Partner', required=True, ondelete='cascade', index=True)
    invoice_date = fields.Date(string='Invoice Date')
    invoice_name = fields.Char(string='Invoice No.')
    invoice_date_due = fields.Date(string='Due Date')
    product_id = fields.Many2one('product.product', string='Product')
    product_name = fields.Char(string='Product Name')
    price_unit = fields.Float(string='Price', digits=(16, 2))
    quantity = fields.Float(string='Quantity', digits=(16, 2))
    price_subtotal = fields.Float(string='Total Amount', digits=(16, 2))
    amount_residual = fields.Float(string='Amount Due', digits=(16, 2))
    sequence = fields.Integer(string='Sequence', default=10)

