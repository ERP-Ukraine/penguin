# coding: utf-8
# Part of PIT Solutions AG. See LICENSE file for full copyright and licensing details.

import logging

from odoo import api, fields, models, _


_logger = logging.getLogger(__name__)


class PaymentIcon(models.Model):
    _inherit = 'payment.icon'
    _order = 'sequence'
    
    sequence = fields.Integer('Sequence', default=10)
    name = fields.Char(translate=True)


class WalleePaymentMethod(models.Model):
    _name = 'wallee.payment.method'
    _description = 'Wallee Payment Method Details'
    _order = 'sequence'

    sequence = fields.Integer('Sequence', default=10)
    name = fields.Many2one('payment.icon', 'Name', required=True)
    acquirer_id = fields.Many2one('payment.acquirer', 'Acquirer', required=True)
    space_id = fields.Integer(string='Space Ref', required=True)
    method_id = fields.Integer(string='Payment Method Ref', required=True)
    image_url = fields.Char('Image Url', size=1024)
    one_click = fields.Boolean(string='oneClick Payment', default=False)
    one_click_mode = fields.Boolean(string='oneClick Payment Mode', default=False)
    payment_method_ref = fields.Float(string='Payment Method', size=15, digits=(15, 0))
    transaction_interface = fields.Char('Transaction Interface')
    active = fields.Boolean(default=True)
    version = fields.Integer(required=True)

    def action_post_data(self):
        for wallee_pay_method in self:
            wallee_acquirer = wallee_pay_method.acquirer_id
