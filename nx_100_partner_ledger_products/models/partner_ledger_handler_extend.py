# -*- coding: utf-8 -*-
from odoo import models


class PartnerLedgerHandlerExtend(models.AbstractModel):
    _inherit = "account.partner.ledger.report.handler"

    def _get_move_products_info(self, aml):
        move = aml.move_id
        if not move or move.move_type not in ("out_invoice", "out_refund", "in_invoice", "in_refund"):
            return "", "", ""

        names, prices, quantities = [], [], []

        for line in move.invoice_line_ids:
            names.append(line.product_id.display_name or line.name or "")
            prices.append("{:,.2f}".format(line.price_unit or 0.0))
            quantities.append("{:,.2f}".format(line.quantity or 0.0))

        sep = "\n"
        return (
            sep.join(names) if names else "",
            sep.join(prices) if prices else "",
            sep.join(quantities) if quantities else "",
        )

    def _get_aml_values(self, options, partner_ids, offset=0, limit=None):
        rslt = super()._get_aml_values(options, partner_ids, offset=offset, limit=limit)
        MoveLine = self.env["account.move.line"].browse

        for _partner_id, lines in rslt.items():
            for line in lines:
                aml = MoveLine(line["id"])
                prod, price, qty = self._get_move_products_info(aml)

                line["nx_product_names"] = prod
                line["nx_product_price"] = price
                line["nx_product_qty"] = qty

        return rslt
