from odoo import _, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # override for enable products from multiple warehouses
    def _cart_lines_stock_update(self, values, **kwargs):
        line_id = values.get('line_id')
        for line in self.order_line:
            if line.product_id.type == 'product' and not line.product_id.allow_out_of_stock_order:
                cart_qty = sum(self.order_line.filtered(lambda p: p.product_id.id == line.product_id.id).mapped('product_uom_qty'))
                # ERPUkraine use multiple warehouses
                warehouse_ids = self.env['website'].get_current_website().sudo().warehouse_ids
                context = dict(warehouse=warehouse_ids.ids)
                available_qty = line.product_id.with_context(context).free_qty
                if (line_id == line.id) and cart_qty > available_qty:
                    qty = available_qty - cart_qty
                    new_val = super(SaleOrder, self.with_context(context))._cart_update(line.product_id.id, line.id, qty, 0, **kwargs)
                    values.update(new_val)

                    # Make sure line still exists, it may have been deleted in super()._cart_update because qty can be <= 0
                    if line.exists() and new_val['quantity']:
                        line.warning_stock = _('You ask for %s products but only %s is available') % (cart_qty, new_val['quantity'])
                        values['warning'] = line.warning_stock
                    else:
                        self.warning_stock = _("Some products became unavailable and your cart has been updated. We're sorry for the inconvenience.")
                        values['warning'] = self.warning_stock
        return values
