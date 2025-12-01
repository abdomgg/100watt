# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Bhagyadev KP (<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
import io
import json
from datetime import datetime

from dateutil.relativedelta import relativedelta
import xlsxwriter

from odoo import api, fields, models
from odoo.tools import date_utils


class AccountPartnerLedger(models.TransientModel):
    """For creating Partner Ledger report"""
    _name = 'account.partner.ledger'
    _description = 'Partner Ledger Report'

    # -------------------------------------------------------------------------
    # Helper: products / prices / quantities for one move
    # -------------------------------------------------------------------------
    def _get_move_products_info(self, move_line):
        """Return 3 strings: products, prices, quantities for the move."""
        move = move_line.move_id
        # Only invoices / bills / refunds usually have products
        if not move or move.move_type not in (
            'out_invoice', 'out_refund', 'in_invoice', 'in_refund'
        ):
            return '', '', ''

        product_names = []
        product_prices = []
        product_quantities = []

        for il in move.invoice_line_ids:
            product_names.append(il.product_id.display_name or il.name or '')
            product_prices.append("{:,.2f}".format(il.price_unit or 0.0))
            product_quantities.append("{:,.2f}".format(il.quantity or 0.0))

        # newline-separated so they look good in PDF/Excel with wrapping
        return (
            '\n'.join(product_names),
            '\n'.join(product_prices),
            '\n'.join(product_quantities),
        )

    # -------------------------------------------------------------------------
    # JSON data for initial load
    # -------------------------------------------------------------------------
    @api.model
    def view_report(self, option, tag):
        fiscal_year = self.env['res.company'].search([]).mapped(
            'account_opening_date'
        )[0].strftime('%Y-%m-%d')
        fiscal_year_start = datetime.strptime(fiscal_year, '%Y-%m-%d').date()

        partner_dict = {}
        partner_totals = {}

        move_line_ids = self.env['account.move.line'].search(
            [
                ('account_type', 'in', ['liability_payable', 'asset_receivable']),
                ('parent_state', '=', 'posted'),
            ]
        )
        partner_ids = move_line_ids.mapped('partner_id')

        for partner in partner_ids:
            total_debit_balance = 0
            total_credit_balance = 0
            balance = 0

            move_line_id = move_line_ids.filtered(lambda x: x.partner_id == partner)
            move_line_list = []

            for move_line in move_line_id:
                if move_line.invoice_date and move_line.invoice_date < fiscal_year_start:
                    total_debit_balance += move_line.debit
                    total_credit_balance += move_line.credit
                    balance = total_debit_balance - total_credit_balance

                move_line_data = move_line.read(
                    [
                        'date',
                        'move_name',
                        'account_type',
                        'debit',
                        'credit',
                        'date_maturity',
                        'account_id',
                        'journal_id',
                        'move_id',
                        'matching_number',
                        'amount_currency',
                    ]
                )
                account_code = move_line.account_id.code
                journal_code = move_line.journal_id.code
                if account_code:
                    move_line_data[0]['jrnl'] = journal_code
                    move_line_data[0]['code'] = account_code

                # add products info
                products, prices, quantities = self._get_move_products_info(move_line)
                move_line_data[0]['products'] = products
                move_line_data[0]['product_prices'] = prices
                move_line_data[0]['product_quantities'] = quantities

                move_line_list.append(move_line_data)

            partner_dict[partner.name] = move_line_list
            currency_id = self.env.company.currency_id.symbol
            partner_totals[partner.name] = {
                'total_debit': round(sum(move_line_id.mapped('debit')), 2),
                'total_credit': round(sum(move_line_id.mapped('credit')), 2),
                'currency_id': currency_id,
                'initial_balance': balance,
                'partner_id': partner.id,
                'move_name': 'Initial Balance',
                'initial_debit': total_debit_balance,
                'initial_credit': total_credit_balance,
            }
            partner_dict['partner_totals'] = partner_totals

        return partner_dict

    # -------------------------------------------------------------------------
    # JSON data for filtered view
    # -------------------------------------------------------------------------
    @api.model
    def get_filter_values(self, partner_id, data_range, account, options):
        if options == {}:
            options = None
        if account == {}:
            account = None

        account_type_domain = []
        if options is None:
            option_domain = ['posted']
        elif 'draft' in options:
            option_domain = ['posted', 'draft']

        if account is None or ('Receivable' in account and 'Payable' in account):
            account_type_domain.extend(['liability_payable', 'asset_receivable'])
        elif 'Receivable' in account:
            account_type_domain.append('asset_receivable')
        elif 'Payable' in account:
            account_type_domain.append('liability_payable')

        partner_dict = {}
        partner_totals = {}

        today = fields.Date.today()
        quarter_start, quarter_end = date_utils.get_quarter(today)
        previous_quarter_start = quarter_start - relativedelta(months=3)
        previous_quarter_end = quarter_start - relativedelta(days=1)

        if not partner_id:
            partner_id = self.env['account.move.line'].search(
                [
                    ('account_type', 'in', account_type_domain),
                    ('parent_state', 'in', option_domain),
                ]
            ).mapped('partner_id').ids

        balance_move_line_ids = []

        for partners in partner_id:
            partner = self.env['res.partner'].browse(partners).name

            # ---- original logic to compute move_line_ids + balance_move_line_ids
            if data_range:
                if data_range == 'month':
                    move_line_ids = self.env['account.move.line'].search(
                        [
                            ('partner_id', '=', partners),
                            ('account_type', 'in', account_type_domain),
                            ('parent_state', 'in', option_domain),
                        ]
                    ).filtered(lambda x: x.date.month == today.month)
                    date_start = today.replace(day=1)
                    balance_move_line_ids = self.env['account.move.line'].search(
                        [
                            ('partner_id', '=', partners),
                            ('account_type', 'in', account_type_domain),
                            ('parent_state', 'in', option_domain),
                            ('invoice_date', '<', date_start),
                        ]
                    )
                elif data_range == 'year':
                    move_line_ids = self.env['account.move.line'].search(
                        [
                            ('partner_id', '=', partners),
                            ('account_type', 'in', account_type_domain),
                            ('parent_state', 'in', option_domain),
                        ]
                    ).filtered(lambda x: x.date.year == today.year)
                    date_start = today.replace(month=1, day=1)
                    balance_move_line_ids = self.env['account.move.line'].search(
                        [
                            ('partner_id', '=', partners),
                            ('account_type', 'in', account_type_domain),
                            ('parent_state', 'in', option_domain),
                            ('invoice_date', '<', date_start),
                        ]
                    )
                elif data_range == 'quarter':
                    move_line_ids = self.env['account.move.line'].search(
                        [
                            ('partner_id', '=', partners),
                            ('account_type', 'in', account_type_domain),
                            ('date', '>=', quarter_start),
                            ('date', '<=', quarter_end),
                            ('parent_state', 'in', option_domain),
                        ]
                    )
                    date_start = quarter_start
                    balance_move_line_ids = self.env['account.move.line'].search(
                        [
                            ('partner_id', '=', partners),
                            ('account_type', 'in', account_type_domain),
                            ('parent_state', 'in', option_domain),
                            ('invoice_date', '<', date_start),
                        ]
                    )
                elif data_range == 'last-month':
                    move_line_ids = self.env['account.move.line'].search(
                        [
                            ('partner_id', '=', partners),
                            ('account_type', 'in', account_type_domain),
                            ('parent_state', 'in', option_domain),
                        ]
                    ).filtered(lambda x: x.date.month == today.month - 1)
                    date_start = today.replace(day=1, month=today.month - 1)
                    balance_move_line_ids = self.env['account.move.line'].search(
                        [
                            ('partner_id', '=', partners),
                            ('account_type', 'in', account_type_domain),
                            ('parent_state', 'in', option_domain),
                            ('invoice_date', '<', date_start),
                        ]
                    )
                elif data_range == 'last-year':
                    move_line_ids = self.env['account.move.line'].search(
                        [
                            ('partner_id', '=', partners),
                            ('account_type', 'in', account_type_domain),
                            ('parent_state', 'in', option_domain),
                        ]
                    ).filtered(lambda x: x.date.year == today.year - 1)
                    date_start = today.replace(day=1, month=1)
                    balance_move_line_ids = self.env['account.move.line'].search(
                        [
                            ('partner_id', '=', partners),
                            ('account_type', 'in', account_type_domain),
                            ('parent_state', 'in', option_domain),
                            ('invoice_date', '<', date_start),
                        ]
                    )
                elif data_range == 'last-quarter':
                    move_line_ids = self.env['account.move.line'].search(
                        [
                            ('partner_id', '=', partners),
                            ('account_type', 'in', account_type_domain),
                            ('date', '>=', previous_quarter_start),
                            ('date', '<=', previous_quarter_end),
                            ('parent_state', 'in', option_domain),
                        ]
                    )
                    date_start = previous_quarter_start
                    balance_move_line_ids = self.env['account.move.line'].search(
                        [
                            ('partner_id', '=', partners),
                            ('account_type', 'in', account_type_domain),
                            ('parent_state', 'in', option_domain),
                            ('invoice_date', '<', date_start),
                        ]
                    )
                elif 'start_date' in data_range and 'end_date' in data_range:
                    start_date = datetime.strptime(
                        data_range['start_date'], '%Y-%m-%d'
                    ).date()
                    end_date = datetime.strptime(
                        data_range['end_date'], '%Y-%m-%d'
                    ).date()
                    move_line_ids = self.env['account.move.line'].search(
                        [
                            ('partner_id', '=', partners),
                            ('account_type', 'in', account_type_domain),
                            ('date', '>=', start_date),
                            ('date', '<=', end_date),
                            ('parent_state', 'in', option_domain),
                        ]
                    )
                    date_start = start_date
                    balance_move_line_ids = self.env['account.move.line'].search(
                        [
                            ('partner_id', '=', partners),
                            ('account_type', 'in', account_type_domain),
                            ('parent_state', 'in', option_domain),
                            ('invoice_date', '<', date_start),
                        ]
                    )
                elif 'start_date' in data_range:
                    start_date = datetime.strptime(
                        data_range['start_date'], '%Y-%m-%d'
                    ).date()
                    move_line_ids = self.env['account.move.line'].search(
                        [
                            ('partner_id', '=', partners),
                            ('account_type', 'in', account_type_domain),
                            ('date', '>=', start_date),
                            ('parent_state', 'in', option_domain),
                        ]
                    )
                    date_start = start_date
                    balance_move_line_ids = self.env['account.move.line'].search(
                        [
                            ('partner_id', '=', partners),
                            ('account_type', 'in', account_type_domain),
                            ('parent_state', 'in', option_domain),
                            ('invoice_date', '<', date_start),
                        ]
                    )
                elif 'end_date' in data_range:
                    end_date = datetime.strptime(
                        data_range['end_date'], '%Y-%m-%d'
                    ).date()
                    move_line_ids = self.env['account.move.line'].search(
                        [
                            ('partner_id', '=', partners),
                            ('account_type', 'in', account_type_domain),
                            ('date', '<=', end_date),
                            ('parent_state', 'in', option_domain),
                        ]
                    )
                    fiscal_year = self.env['res.company'].search([]).mapped(
                        'account_opening_date'
                    )[0].strftime('%Y-%m-%d')
                    date_start = datetime.strptime(fiscal_year, '%Y-%m-%d').date()
                    balance_move_line_ids = self.env['account.move.line'].search(
                        [
                            ('partner_id', '=', partners),
                            ('account_type', 'in', account_type_domain),
                            ('parent_state', 'in', option_domain),
                            ('invoice_date', '<', date_start),
                        ]
                    )
            else:
                move_line_ids = self.env['account.move.line'].search(
                    [
                        ('partner_id', '=', partners),
                        ('account_type', 'in', account_type_domain),
                        ('parent_state', 'in', option_domain),
                    ]
                )

            total_debit_balance = 0
            total_credit_balance = 0
            balance = 0
            move_line_list = []

            for move_line in move_line_ids:
                move_line_data = move_line.read(
                    [
                        'date',
                        'move_name',
                        'account_type',
                        'debit',
                        'credit',
                        'date_maturity',
                        'account_id',
                        'journal_id',
                        'move_id',
                        'matching_number',
                        'amount_currency',
                    ]
                )
                account_code = move_line.account_id.code
                journal_code = move_line.journal_id.code
                if account_code:
                    move_line_data[0]['jrnl'] = journal_code
                    move_line_data[0]['code'] = account_code

                # add products info
                products, prices, quantities = self._get_move_products_info(move_line)
                move_line_data[0]['products'] = products
                move_line_data[0]['product_prices'] = prices
                move_line_data[0]['product_quantities'] = quantities

                move_line_list.append(move_line_data)

            for remaining_move in balance_move_line_ids:
                if remaining_move.invoice_date and remaining_move.invoice_date < date_start:
                    total_debit_balance += remaining_move.debit
                    total_credit_balance += remaining_move.credit
                    balance = total_debit_balance - total_credit_balance

            partner_dict[partner] = move_line_list
            currency_id = self.env.company.currency_id.symbol
            partner_totals[partner] = {
                'total_debit': round(sum(move_line_ids.mapped('debit')), 2),
                'total_credit': round(sum(move_line_ids.mapped('credit')), 2),
                'currency_id': currency_id,
                'partner_id': partners,
                'initial_balance': balance,
                'move_name': 'Initial Balance',
                'initial_debit': total_debit_balance,
                'initial_credit': total_credit_balance,
            }
            partner_dict['partner_totals'] = partner_totals

        return partner_dict

    # -------------------------------------------------------------------------
    # XLSX export
    # -------------------------------------------------------------------------
    @api.model
    def get_xlsx_report(self, data, response, report_name, report_action):
        data = json.loads(data)
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        start_date = data['filters']['start_date'] or ''
        end_date = data['filters']['end_date'] or ''
        sheet = workbook.add_worksheet()

        # formats
        head = workbook.add_format({'font_size': 15, 'align': 'center', 'bold': True})
        head_highlight = workbook.add_format({'font_size': 10, 'align': 'center', 'bold': True})
        sub_heading = workbook.add_format({
            'align': 'center', 'bold': True, 'font_size': '10px',
            'border': 1, 'bg_color': '#D3D3D3', 'border_color': 'black'
        })
        filter_head = workbook.add_format({
            'align': 'center', 'bold': True, 'font_size': '10px',
            'border': 1, 'bg_color': '#D3D3D3', 'border_color': 'black'
        })
        filter_body = workbook.add_format({'align': 'center', 'bold': True, 'font_size': '10px'})
        side_heading_sub = workbook.add_format({
            'align': 'left', 'bold': True, 'font_size': '10px',
            'border': 1, 'border_color': 'black'
        })
        side_heading_sub.set_indent(1)
        txt_name = workbook.add_format({'font_size': '10px', 'border': 1})
        txt_name.set_indent(2)
        txt_name.set_text_wrap()

        # column widths
        sheet.set_column(0, 0, 30)
        sheet.set_column(1, 1, 20)
        sheet.set_column(2, 2, 15)
        sheet.set_column(3, 3, 15)

        col = 0
        sheet.write('A1:B1', report_name, head)
        sheet.write('B3:B4', 'Date Range', filter_head)
        sheet.write('B4:B4', 'Partners', filter_head)
        sheet.write('B5:B4', 'Accounts', filter_head)
        sheet.write('B6:B4', 'Options', filter_head)

        if start_date or end_date:
            sheet.merge_range('C3:G3', f"{start_date} to {end_date}", filter_body)

        if data['filters']['partner']:
            display_names = [
                partner.get('display_name', 'undefined')
                for partner in data['filters']['partner']
            ]
            sheet.merge_range('C4:G4', ', '.join(display_names), filter_body)

        if data['filters']['account']:
            account_keys = list(data['filters']['account'].keys())
            sheet.merge_range('C5:G5', ', '.join(account_keys), filter_body)

        if data['filters']['options']:
            option_keys = list(data['filters']['options'].keys())
            sheet.merge_range('C6:G6', ', '.join(option_keys), filter_body)

        def format_number(value):
            if value is None:
                return "0.00"
            return "{:,.2f}".format(float(value))

        if data and report_action == 'dynamic_accounts_report.action_partner_ledger':
            sheet.write(8, col, ' ', sub_heading)
            sheet.write(8, col + 1, 'JNRL', sub_heading)
            sheet.write(8, col + 2, 'Account', sub_heading)
            sheet.merge_range('D9:E9', 'Ref', sub_heading)
            sheet.merge_range('F9:G9', 'Due Date', sub_heading)
            sheet.merge_range('H9:I9', 'Debit', sub_heading)
            sheet.merge_range('J9:K9', 'Credit', sub_heading)
            sheet.merge_range('L9:M9', 'Balance', sub_heading)

            # new columns
            sheet.write(8, col + 13, 'Products', sub_heading)
            sheet.write(8, col + 14, 'Price', sub_heading)
            sheet.write(8, col + 15, 'Quantity', sub_heading)
            sheet.set_column(13, 13, 30)
            sheet.set_column(14, 15, 15)

            row = 8
            partners = data.get('partners', []) or []

            for partner in partners:
                row += 1
                total_debit = data['total'][partner]['total_debit'] if data['total'] and partner in data['total'] else 0
                total_credit = data['total'][partner]['total_credit'] if data['total'] and partner in data['total'] else 0
                balance = total_debit - total_credit

                sheet.write(row, col, partner, txt_name)
                sheet.write(row, col + 1, ' ', txt_name)
                sheet.write(row, col + 2, ' ', txt_name)
                sheet.merge_range(row, col + 3, row, col + 4, ' ', txt_name)
                sheet.merge_range(row, col + 5, row, col + 6, ' ', txt_name)
                sheet.merge_range(row, col + 7, row, col + 8, format_number(total_debit), txt_name)
                sheet.merge_range(row, col + 9, row, col + 10, format_number(total_credit), txt_name)
                sheet.merge_range(row, col + 11, row, col + 12, format_number(balance), txt_name)

                initial_balance = data['total'][partner]['initial_balance'] if data['total'] and partner in data['total'] else 0
                if initial_balance != 0:
                    row += 1
                    initial_debit = data['total'][partner]['initial_debit'] if data['total'] and partner in data['total'] else 0
                    initial_credit = data['total'][partner]['initial_credit'] if data['total'] and partner in data['total'] else 0

                    sheet.write(row, col, '', txt_name)
                    sheet.write(row, col + 1, ' ', txt_name)
                    sheet.write(row, col + 2, ' ', txt_name)
                    sheet.merge_range(row, col + 3, row, col + 4, 'Initial Balance', head_highlight)
                    sheet.merge_range(row, col + 5, row, col + 6, ' ', txt_name)
                    sheet.merge_range(row, col + 7, row, col + 8, format_number(initial_debit), txt_name)
                    sheet.merge_range(row, col + 9, row, col + 10, format_number(initial_credit), txt_name)
                    sheet.merge_range(row, col + 11, row, col + 12, format_number(initial_balance), txt_name)

                for rec in data['data'][partner]:
                    row += 1
                    sheet.write(row, col, rec[0]['date'], txt_name)
                    sheet.write(row, col + 1, rec[0]['jrnl'], txt_name)
                    sheet.write(row, col + 2, rec[0]['code'], txt_name)
                    sheet.merge_range(row, col + 3, row, col + 4, rec[0]['move_name'], txt_name)
                    sheet.merge_range(row, col + 5, row, col + 6, rec[0]['date_maturity'] or '', txt_name)
                    sheet.merge_range(row, col + 7, row, col + 8, format_number(rec[0]['debit']), txt_name)
                    sheet.merge_range(row, col + 9, row, col + 10, format_number(rec[0]['credit']), txt_name)
                    sheet.merge_range(row, col + 11, row, col + 12, ' ', txt_name)

                    sheet.write(row, col + 13, rec[0].get('products', ''), txt_name)
                    sheet.write(row, col + 14, rec[0].get('product_prices', ''), txt_name)
                    sheet.write(row, col + 15, rec[0].get('product_quantities', ''), txt_name)

            row += 1
            grand_total_debit = data['grand_total']['total_debit'] if data['grand_total'] and data['grand_total']['total_debit'] is not None else 0
            grand_total_credit = data['grand_total']['total_credit'] if data['grand_total'] and data['grand_total']['total_credit'] is not None else 0
            grand_balance = grand_total_debit - grand_total_credit

            sheet.merge_range(row, col, row, col + 6, 'Total', filter_head)
            sheet.merge_range(row, col + 7, row, col + 8, format_number(grand_total_debit), filter_head)
            sheet.merge_range(row, col + 9, row, col + 10, format_number(grand_total_credit), filter_head)
            sheet.merge_range(row, col + 11, row, col + 12, format_number(grand_balance), filter_head)

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
