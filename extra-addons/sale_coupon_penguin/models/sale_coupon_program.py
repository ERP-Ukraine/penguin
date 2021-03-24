# -*- coding: utf-8 -*-
from odoo import models


class SaleCouponProgram(models.Model):
    _inherit = 'sale.coupon.program'

    def _check_promo_code(self, order, coupon_code):
        if not self.promo_code and self in order.no_code_promo_program_ids:
            return {}
        else:
            return super()._check_promo_code(order, coupon_code)
