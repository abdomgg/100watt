from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    qty_on_hand = fields.Float(
        string='On Hand',
        compute='_compute_qty_on_hand',
        digits='Product Unit of Measure',
        readonly=True,
        help='Current available quantity for the selected product in the order warehouse.',
    )

    def _get_available_qty_for_order(self):
        """Return available quantity considering the order warehouse."""
        self.ensure_one()
        product = self.product_id
        warehouse = self.order_id.warehouse_id
        location = warehouse.lot_stock_id if warehouse else None
        if not location:
            location = product.property_stock_inventory
        qty = self.env['stock.quant']._get_available_quantity(product, location, allow_negative=True)
        return product.uom_id._compute_quantity(qty, self.product_uom)

    def _compute_qty_on_hand(self):
        for line in self:
            if not line.product_id:
                line.qty_on_hand = 0.0
                continue
            product = line.product_id
            warehouse = line.order_id.warehouse_id
            location = warehouse.lot_stock_id if warehouse else None
            if not location:
                location = product.property_stock_inventory
            qty = self.env['stock.quant']._get_available_quantity(product, location, allow_negative=True)
            line.qty_on_hand = product.uom_id._compute_quantity(qty, line.product_uom or product.uom_id)


