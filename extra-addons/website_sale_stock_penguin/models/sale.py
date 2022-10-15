# -*- coding: utf-8 -*-
from odoo import _, api, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # Overrriden:
    # Enable products from multiple werahouses
    def _cart_lines_stock_update(self, values, **kwargs):
        line_id = values.get('line_id')
        for line in self.order_line:
            if line.product_id.type == 'product' and not line.product_id.allow_out_of_stock_order:
                cart_qty = sum(self.order_line.filtered(lambda p: p.product_id.id == line.product_id.id).mapped('product_uom_qty'))
                # ERPUkraine: change in context, do not use warehouse
                if (line_id == line.id) and cart_qty > line.product_id.with_context(warehouse=None).free_qty:
                    qty = line.product_id.with_context(warehouse=None).free_qty - cart_qty
                    new_val = super(SaleOrder, self.with_context(warehouse=None))._cart_update(line.product_id.id, line.id, qty, 0, **kwargs)
                    values.update(new_val)

                    # Make sure line still exists, it may have been deleted in super()_cartupdate because qty can be <= 0
                    if line.exists() and new_val['quantity']:
                        line.warning_stock = _('You ask for %s products but only %s is available') % (cart_qty, new_val['quantity'])
                        values['warning'] = line.warning_stock
                    else:
                        self.warning_stock = _("Some products became unavailable and your cart has been updated. We're sorry for the inconvenience.")
                        values['warning'] = self.warning_stock
        return values

    @api.onchange('pricelist_id')
    def _onchange_pricelist_id(self):
        if self.pricelist_id.warehouse_id:
            self.warehouse_id = self.pricelist_id.warehouse_id
        if self.pricelist_id.salesperson_id:
            self.user_id = self.pricelist_id.salesperson_id
