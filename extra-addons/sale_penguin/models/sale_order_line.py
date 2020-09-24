from odoo import fields, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    external_id = fields.Integer('External ID', copy=False)

    penguin_net_price_pc = fields.Monetary(string='Net Price/pc', compute='_compute_penguin_net_price_pc')

    def _compute_penguin_net_price_pc(self):
        for line in self:
            price_info = line.tax_id.compute_all(
                line.price_unit * (1 - (line.discount or 0.0) / 100.0),
                line.order_id.currency_id,
                1,  # quantity
                product=line.product_id,
                partner=line.order_id.partner_shipping_id,
            )
            line.penguin_net_price_pc = price_info['total_excluded']
