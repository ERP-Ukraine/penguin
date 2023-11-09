# -*- coding: utf-8 -*-
from odoo import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    mailing_contact_ids = fields.One2many('mailing.contact', 'partner_id', string='Mailing Contact')
