# -*- coding: utf-8 -*-
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    contacts_mass_mailing_list = fields.Many2one(
        'mailing.list',
        related='company_id.contacts_mass_mailing_list',
        string='Default Mailing List',
        readonly=False)
