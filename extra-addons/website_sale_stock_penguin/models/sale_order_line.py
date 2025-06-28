from odoo import models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    # PEN-140: use warehouse according to customer country
    def _get_multi_warehouse_procurements(self, line, product_qty, procurement_uom, values, precision, warehouse_ids=None):
        shipping_country_id = line.order_id.partner_shipping_id.country_id
        if warehouse_ids and shipping_country_id:
            warehouse_ids = warehouse_ids.sorted(key=lambda w: shipping_country_id in w.country_ids, reverse=True)
        return super()._get_multi_warehouse_procurements(line, product_qty, procurement_uom, values, precision, warehouse_ids)
