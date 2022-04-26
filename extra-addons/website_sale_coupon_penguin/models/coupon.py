# -*- coding: utf-8 -*-
from odoo import models


class Coupon(models.Model):
    _inherit = 'coupon.coupon'

    def _check_coupon_code(self, order_date, partner_id, **kwargs):
        # We need to apply coupons on offline sales orders
        order = kwargs.get('order', False)
        if order and self.program_id.website_id and not order.website_id:
            order.website_id = self.program_id.website_id
        return super()._check_coupon_code(order_date, partner_id, **kwargs)
