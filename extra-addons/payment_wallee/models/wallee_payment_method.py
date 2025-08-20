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

from odoo import fields, models


class WalleePaymentMethod(models.Model):
    _name = 'wallee.payment.method'
    _description = 'Wallee Payment Method Details'
    _order = 'sequence'

    sequence = fields.Integer(default=10)
    name = fields.Many2one('payment.method', required=True)
    acquirer_id = fields.Many2one('payment.provider', 'Acquirer', required=True)
    space_id = fields.Integer(string='Space Ref', required=True)
    method_id = fields.Integer(string='Payment Method Ref', required=True)
    image_url = fields.Char(size=1024)
    one_click = fields.Boolean(string='oneClick Payment', default=False)
    one_click_mode = fields.Boolean(string='oneClick Payment Mode', default=False)
    payment_method_ref = fields.Float(string='Payment Method', digits=(15, 0))
    transaction_interface = fields.Char()
    active = fields.Boolean(default=True)
    version = fields.Integer(required=True)
