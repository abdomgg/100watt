from odoo import models, fields, api, _


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"


    product_code_id = fields.Many2one(
        'product.code',
        string="Product Code"
    )

    # ---------------------------------------------------------
    # onchange product_id → fill product_code
    # ---------------------------------------------------------
    @api.onchange("product_id")
    def _onchange_product_id_set_code(self):
        if self.product_id:
            self.product_code_id = self.product_id.product_tmpl_id.product_code_id
        else:
            self.product_code_id = False

    # ---------------------------------------------------------
    # onchange product_code → find product
    # ---------------------------------------------------------
    @api.onchange("product_code_id")
    def _onchange_product_code_id(self):
        if not self.product_code_id:
            self.product_id = False
            return

        tmpl = self.product_code_id.product_tmpl_id
        self.product_id = tmpl.product_variant_ids[:1]
