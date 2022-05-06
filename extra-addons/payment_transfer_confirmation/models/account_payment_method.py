# -*- coding: utf-8 -*-
from odoo import api, models


class AccountPaymentMethod(models.Model):
    _inherit = 'account.payment.method'

    @api.model
    def _get_payment_method_information(self):
        methods = super()._get_payment_method_information()
        methods['transfer'] = {'mode': 'multi', 'domain': [('type', '=', 'bank')]}
        return methods
