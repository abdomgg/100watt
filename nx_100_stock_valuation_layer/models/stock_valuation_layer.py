from odoo import models, fields, api


class StockValuationLayer(models.Model):
    _inherit = 'stock.valuation.layer'

    product_qty_available = fields.Float(
        string='On Hand',
        compute='_compute_product_qty_available',
        store=False,
        help='Current on-hand quantity for this product'
    )

    total_inventory_value = fields.Monetary(
        string='القيمة الكلية المخزنية',
        compute='_compute_total_inventory_value',
        store=False,
        currency_field='currency_id',
        help='Total inventory value (on-hand quantity × unit cost)'
    )

    @api.depends('product_id')
    def _compute_product_qty_available(self):
        for record in self:
            if record.product_id:
                record.product_qty_available = record.product_id.qty_available
            else:
                record.product_qty_available = 0.0

    @api.depends('product_id', 'product_id.qty_available', 'unit_cost')
    def _compute_total_inventory_value(self):
        for record in self:
            if record.product_id and record.unit_cost:
                record.total_inventory_value = record.product_id.qty_available * record.unit_cost
            else:
                record.total_inventory_value = 0.0
