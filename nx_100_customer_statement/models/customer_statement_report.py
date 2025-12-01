# -*- coding: utf-8 -*-
from odoo import models
from types import SimpleNamespace


class CustomerStatementReport(models.AbstractModel):
    _name = 'report.nx_100_customer_statement.customer_statement_pdf'
    _description = 'Customer Statement Report'

    def _get_report_values(self, docids, data=None):
        docs = self.env['res.partner'].browse(docids)

        all_statement_lines = []
        for partner in docs:
            all_statement_lines.append(self._get_statement_lines(partner))

        return {
            'doc_ids': docids,
            'doc_model': 'res.partner',
            'docs': docs,
            'all_statement_lines': all_statement_lines,
        }

    def _get_statement_lines(self, partner):
        """
        Build lines from the same records used in the Customer Statement tab:
        partner.invoice_line_statement_ids
        (same as your list view).
        """
        lines = partner.invoice_line_statement_ids.sorted(
            key=lambda l: (
                l.statement_invoice_date or l.date or False,
                l.move_id.id,
                l.id,
            )
        )

        statement_lines = []

        for line in lines:
            move = line.move_id
            currency = move.currency_id or move.company_currency_id
            currency_symbol = ''  # We will not include the currency symbol 'LE'

            product_name = line.product_id.display_name or line.name or ''

            # Check for payment-related terms
            if any(term in product_name.lower() for term in
                   ['payment', 'down payment', 'manual payment', '14%', 'الدفع اليدوي']):
                # Completely omit product, price, and quantity for payment-related terms
                product_name = ''  # Blank product name
                price_unit = ''  # Leave price blank
                quantity = ''  # Leave quantity blank
            else:
                price_unit = '{:,.2f}'.format(line.price_unit or 0.0)
                quantity = '{:,.2f}'.format(line.quantity or 0.0)

            # Append the statement line with the adjusted values
            statement_lines.append(SimpleNamespace(
                invoice_date=(
                    line.statement_invoice_date.strftime('%Y-%m-%d')
                    if line.statement_invoice_date else ''
                ),
                invoice_name=line.statement_invoice_name or '',
                product_name=product_name,
                price_unit=price_unit,  # Price with no 'LE'
                quantity=quantity,  # Quantity with no 'LE'
                price_subtotal='{:,.2f}'.format(line.price_subtotal or 0.0),
                invoice_date_due=(
                    line.statement_invoice_date_due.strftime('%Y-%m-%d')
                    if line.statement_invoice_date_due else ''
                ),
                total_amount='{:,.2f}'.format(
                    line.statement_amount_total_signed or 0.0
                ),
                amount_residual='{:,.2f}'.format(
                    line.statement_amount_residual_signed or 0.0
                ),
                currency_symbol=currency_symbol,  # No currency symbol
            ))

        return statement_lines


