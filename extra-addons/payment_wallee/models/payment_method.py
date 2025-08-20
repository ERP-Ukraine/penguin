# -*- coding: utf-8 -*-
#################################################################################
# Author      : PIT Solutions AG. (<https://www.pitsolutions.com/>)
# Copyright(c): 2019 - Present PIT Solutions AG.
# License URL : https://www.webshopextension.com/en/licence-agreement/
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <https://www.webshopextension.com/en/licence-agreement/>
#################################################################################

from odoo import api, fields, models


class PaymentMethod(models.Model):
    _inherit = 'payment.method'

    sequence = fields.Integer(default=10)
    name = fields.Char(translate=True)
    is_wallee = fields.Boolean(string='Wallee Payment', default=False)

    @api.model
    def get_wallee_payment_methods(self, methods):
        return methods.filtered(lambda i: i.is_wallee)

    @api.model
    def get_non_wallee_payment_methods(self, methods):
        return methods.filtered(lambda i: not i.is_wallee)
