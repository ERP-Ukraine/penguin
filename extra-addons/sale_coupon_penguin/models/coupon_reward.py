# -*- coding: utf-8 -*-
import logging

from odoo import fields, models, _

_logger = logging.getLogger(__name__)


class CouponReward(models.Model):
    _inherit = 'coupon.reward'

    reward_type = fields.Selection(selection_add=[('penguin_promocode_amount', 'Penguin Promocode Amount')])

    def name_get(self):
        reward_names = super().name_get()
        peng_rewards = self.filtered(lambda r: r.reward_type == 'penguin_promocode_amount')
        return [(reward_id, reward_id in peng_rewards.ids and _('Penguin Promocode Amount') or name)
                                                                for reward_id, name in reward_names]
