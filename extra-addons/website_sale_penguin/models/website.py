# -*- coding: utf-8 -*-
import logging

from odoo import fields, models, http
from odoo.exceptions import UserError
from odoo.tests.common import Form

_logger = logging.getLogger(__name__)


# PEN-74: update pricelist and prices for client after logging in
class Website(models.Model):
    _inherit = 'website'

    address_country_group_ids = fields.Many2many('res.country.group', string='Address Country Groups')
