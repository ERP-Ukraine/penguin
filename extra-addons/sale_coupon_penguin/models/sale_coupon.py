# -*- coding: utf-8 -*-
from dateutil.relativedelta import relativedelta
from odoo import fields, models


class SaleCoupon(models.Model):
    _inherit = 'sale.coupon'

    discount_amount = fields.Float()
    currency_id = fields.Many2one('res.currency', related='order_id.currency_id')

    def _compute_expiration_date(self):
        for coupon in self:
            # FIX for promo program: set duration to 365
            # originally duration was used on coupon programs only
            duration = coupon.program_id.validity_duration or 365
            coupon.expiration_date = (coupon.create_date + relativedelta(days=duration)).date()

    def _check_coupon_code(self, order):
        # We do not check is a coupon belongs to particular partner
        # because you can give it as a gift
        if self.partner_id and self.partner_id != order.partner_id:
            self.partner_id = order.partner_id
        return super()._check_coupon_code(order)
