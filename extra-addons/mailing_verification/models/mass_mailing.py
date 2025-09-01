# -*- coding: utf-8 -*-
from datetime import datetime, timedelta

from odoo import api, fields, models


class MassMailingContact(models.Model):
    _inherit = 'mailing.contact'

    is_verified = fields.Boolean(default=True)

    @api.model
    def _cron_delete_not_verified_contacts(self):
        mailing_contacts = self.env['mailing.contact'].search(
            [('is_verified', '=', False)]
        )
        for mailing_contact in mailing_contacts:
            if datetime.now() - mailing_contact.create_date > timedelta(days=7):
                if mailing_contact.partner_id.exists():
                    if mailing_contact.partner_id.user_ids.exists():
                        mailing_contact.partner_id.user_ids.unlink()
                    mailing_contact.partner_id.unlink()
                mailing_contact.unlink()
        res_partners = self.env['res.partner'].search([('is_verified', '=', False)])
        for partner in res_partners:
            if datetime.now() - partner.create_date > timedelta(days=7):
                if partner.user_ids.exists():
                    partner.user_ids.unlink()
                partner.unlink()

        self.env['contact.verification'].search(
            [('create_date', '<', datetime.now() - timedelta(days=7))]
        ).unlink()
