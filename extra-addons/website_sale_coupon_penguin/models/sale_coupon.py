# -*- coding: utf-8 -*-
from odoo import models


class SaleCoupon(models.Model):
    _inherit = 'sale.coupon'

    def _check_coupon_code(self, order):
        # We need to apply coupons on offline sales orders
        if self.program_id.website_id and not order.website_id:
            order.website_id = self.program_id.website_id
        return super()._check_coupon_code(order)
