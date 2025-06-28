# -*- coding: utf-8 -*-
from odoo import api, fields, models


class Company(models.Model):
    _inherit = 'res.company'

    @api.model
    def _default_contacts_mailing_list(self):
        mailing_list = self.env['mailing.list'].search([
            ('name', '=', 'Newsletter')], limit=1)
        if not mailing_list:
            self.env['mailing.list'].create({'name': 'Newsletter'})
        return mailing_list

    contacts_mass_mailing_list = fields.Many2one(
        'mailing.list',
        readonly=False,
        default=_default_contacts_mailing_list)
