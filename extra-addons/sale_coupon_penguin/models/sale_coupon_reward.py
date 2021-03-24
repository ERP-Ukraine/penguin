# -*- coding: utf-8 -*-
from odoo import fields, models, _


class SaleCouponReward(models.Model):
    _inherit = 'sale.coupon.reward'

    reward_type = fields.Selection(selection_add=[('penguin_promocode_amount', 'Penguin Promocode Amount')])

    def name_get(self):
        result = []
        reward_names = super(SaleCouponReward, self).name_get()
        computed_coupon_reward_ids = self.filtered(lambda reward: reward.reward_type == 'computed_coupon').ids
        for res in reward_names:
            result.append((res[0], res[0] in computed_coupon_reward_ids and _("Penguin Promocode Amount") or res[1]))
        return result
