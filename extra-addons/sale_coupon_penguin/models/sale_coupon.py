# -*- coding: utf-8 -*-

from dateutil.relativedelta import relativedelta
from odoo import models


class SaleCoupon(models.Model):
    _inherit = 'sale.coupon'

    def _compute_expiration_date(self):
        for coupon in self:
            # FIX for promo program: set duration to 365
            # originally duration was used on coupon programs only
            duration = coupon.program_id.validity_duration or 365
            coupon.expiration_date = (coupon.create_date + relativedelta(days=duration)).date()
