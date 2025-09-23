# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import datetime
from odoo import api, fields, models


class Event(models.Model):
    _inherit = 'event.event'

    url = fields.Char(string="URL of the event")
    url_label = fields.Char(string="URL's label of the event")
