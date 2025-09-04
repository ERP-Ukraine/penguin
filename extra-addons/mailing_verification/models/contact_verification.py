from datetime import datetime
from urllib.parse import urljoin
from uuid import uuid4

from odoo import api, fields, models


class ContactVerification(models.Model):
    _name = 'contact.verification'
    _description = 'Contact Verification'

    mailing_contact_id = fields.Many2one('mailing.contact')
    partner_id = fields.Many2one('res.partner')
    secret_code = fields.Char(default=lambda self: uuid4())
    create_date = fields.Datetime(default=datetime.now())
    company_id = fields.Many2one(
        'res.partner', default=lambda self: self.env.company.id
    )
    email = fields.Char(compute='_compute_email')
    name = fields.Char(compute='_compute_name')
    confirmation_link = fields.Char(compute='_compute_confirmation_link')

    @api.depends('partner_id', 'mailing_contact_id')
    def _compute_email(self):
        for verification in self:
            if verification.partner_id:
                verification.email = verification.partner_id.email
            elif verification.mailing_contact_id:
                verification.email = verification.mailing_contact_id.email

    @api.depends('partner_id', 'mailing_contact_id')
    def _compute_name(self):
        for verification in self:
            if verification.partner_id:
                verification.name = verification.partner_id.name
            elif verification.mailing_contact_id:
                verification.name = verification.mailing_contact_id.name

    @api.depends('secret_code')
    def _compute_confirmation_link(self):
        base_url = urljoin(
            self.env['ir.config_parameter'].sudo().get_param('web.base.url'),
            '/mail/verification/',
        )
        for verification in self:
            verification.confirmation_link = urljoin(base_url, verification.secret_code)
