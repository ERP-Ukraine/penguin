from odoo.addons.website_sale_stock.controllers import main as wss_controller

from odoo import http, _
from odoo.http import request
from odoo.exceptions import ValidationError


class PaymentPortalPenguin(wss_controller.PaymentPortal):

    # Overrriden:
    # Enable products from multiple werahouses
    @http.route()
    def shop_payment_transaction(self, *args, **kwargs):
        """ Payment transaction override to double check cart quantities before
        placing the order
        """
        order = request.website.sale_get_order()
        values = []
        for line in order.order_line:
            if line.product_id.type == 'product' and not line.product_id.allow_out_of_stock_order:
                cart_qty = sum(order.order_line.filtered(lambda p: p.product_id.id == line.product_id.id).mapped('product_uom_qty'))
                # ERPUkraine: change in context, do not use warehouse
                avl_qty = line.product_id.with_context(warehouse=None).free_qty
                if cart_qty > avl_qty:
                    values.append(_(
                        'You ask for %(quantity)s products but only %(available_qty)s is available',
                        quantity=cart_qty,
                        available_qty=avl_qty if avl_qty > 0 else 0
                    ))
        if values:
            raise ValidationError('. '.join(values) + '.')
        # ERPUkraine: do not call super() on previous controller
        return super(wss_controller.PaymentPortal, self).shop_payment_transaction(*args, **kwargs)
