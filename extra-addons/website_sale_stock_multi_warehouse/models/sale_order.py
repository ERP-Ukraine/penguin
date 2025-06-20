from odoo import models


import logging
_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _get_cart_and_free_qty(self, product, line=None):
        self.ensure_one()
        if not line and not product:
            return 0, 0
        cart_qty = sum(self._get_common_product_lines(line, product).mapped('product_uom_qty'))
        # ERPUkraine use multiple warehouses
        free_qty = 0
        warehouse_ids =  self.sudo().company_id.warehouse_ids # line.company_id.warehouse_ids
        for warehouse_id in warehouse_ids:
            free_qty += (product or line.product_id).with_context(warehouse=warehouse_id.id).free_qty
        #
        return cart_qty, free_qty
