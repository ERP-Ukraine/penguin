from odoo.addons.website_sale_stock.controllers.main import PaymentPortal

from odoo import http, _
from odoo.http import request
from odoo.exceptions import ValidationError


class MWPaymentPortal(PaymentPortal):

    # override to enable products from multiple warehouses
    @http.route()
    def shop_payment_transaction(self, *args, **kwargs):
        """ Payment transaction override to double check cart quantities before
        placing the order
        """
        order = request.website.sale_get_order()
        values = []
        for line in order.order_line:
            if line.product_id.type == 'product' and not line.product_id.allow_out_of_stock_order:
                cart_qty = sum(order.order_line.filtered(
                    lambda p: p.product_id.id == line.product_id.id).mapped('product_uom_qty'))
                # ERPUkraine use all warehouses from current website
                avl_qty = line.product_id.with_context(warehouse=request.website.sudo().company_id.warehouse_ids.ids).free_qty
                # ERPUkraine end of custom code
                if cart_qty > avl_qty:
                    values.append(_(
                        'You ask for %(quantity)s products but only %(available_qty)s is available',
                        quantity=cart_qty,
                        available_qty=avl_qty if avl_qty > 0 else 0
                    ))
        if values:
            raise ValidationError('. '.join(values) + '.')
        # ERPUkraine: do not call super() on previous controller
        return super(PaymentPortal, self).shop_payment_transaction(*args, **kwargs)
