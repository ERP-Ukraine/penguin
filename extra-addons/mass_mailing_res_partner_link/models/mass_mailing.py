# -*- coding: utf-8 -*-
from odoo import api, models, fields


class MassMailingContact(models.Model):
    _inherit = 'mailing.contact'

    partner_id = fields.Many2one('res.partner', string='Partner')
    contact_type = fields.Selection(selection=[('person', 'Individual'), ('company', 'Company')])

    @api.model
    def _cron_update_mailing_contacts(self):
        partners = self.env['res.partner'].search([])

        for partner in partners:
            if partner.email:
                mailing_contact = self.env['mailing.contact'].search([('email', '=', partner.email)])

                if not mailing_contact:
                    self.env['mailing.contact'].create({
                        'partner_id': partner.id,
                        'name': partner.name,
                        'email': partner.email,
                        'country_id': partner.country_id.id,
                        'title_id': partner.title.id,
                        'contact_type': partner.company_type,
                    })
                else:
                    mailing_contact.write({
                        'partner_id': partner.id,
                        'name': partner.name,
                        'email': partner.email,
                        'country_id': partner.country_id.id,
                        'title_id': partner.title.id,
                        'contact_type': partner.company_type,
                    })
