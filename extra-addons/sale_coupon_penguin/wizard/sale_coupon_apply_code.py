# -*- coding: utf-8 -*-
from odoo import models


class SaleCouponApplyCode(models.TransientModel):
    _inherit = 'sale.coupon.apply.code'

    def apply_coupon(self, order, coupon_code):
        coupon = self.env['sale.coupon'].search([('code', '=', coupon_code)])
        if coupon.program_id.reward_type == 'penguin_promocode_amount':
            ctx = self.env.context.copy()
            ctx.update({'penguin_coupon_code': coupon_code})
            order = order.with_context(ctx)
        return super().apply_coupon(order, coupon_code)
