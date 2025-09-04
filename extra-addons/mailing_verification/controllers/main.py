# -*- coding: utf-8 -*-

import logging

from odoo import _, http, tools
from odoo.addons.website_mass_mailing.controllers.main import MassMailController
from odoo.http import request

_logger = logging.getLogger(__name__)


class MassMailControllerExtended(MassMailController):
    @staticmethod
    def subscribe_to_newsletter(
        subscription_type, value, list_id, fname, address_name=None
    ):
        ContactSubscription = request.env['mailing.subscription'].sudo()
        Contacts = request.env['mailing.contact'].sudo()
        if subscription_type == 'email':
            name, value = tools.parse_contact_from_email(value)
            if not name:
                name = address_name
        elif subscription_type == 'mobile':
            name = value

        subscription = ContactSubscription.search(
            [('list_id', '=', int(list_id)), (f'contact_id.{fname}', '=', value)],
            limit=1,
        )
        if not subscription:
            # inline add_to_list as we've already called half of it
            contact_id = Contacts.search([(fname, '=', value)], limit=1)
            if not contact_id:
                # ERP start
                # add is_verified False
                contact_id = Contacts.create(
                    {'name': name, fname: value, 'is_verified': False}
                )
                # send verification email with link
                contact_verification = (
                    request.env['contact.verification']
                    .sudo()
                    .create({'mailing_contact_id': contact_id.id})
                )
                try:
                    template_id = request.env.ref(
                        'mailing_verification.mail_verification_email'
                    )
                    template_id.sudo().send_mail(
                        contact_verification.id, force_send=True
                    )
                except Exception as e:
                    _logger.info(_('Error! Email cannot be send %s', str(e)))
                # ERP end
            ContactSubscription.create(
                {'contact_id': contact_id.id, 'list_id': int(list_id)}
            )
        elif subscription.opt_out:
            subscription.opt_out = False
        # add email to session
        request.session[f'mass_mailing_{fname}'] = value


class ContactVerificationController(http.Controller):
    @http.route(
        '/mail/verification/<string:verification_number>',
        auth='public',
        website=True,
        methods=['GET'],
    )
    def verification(self, verification_number, **kwargs):
        contact_verification = (
            request.env['contact.verification']
            .sudo()
            .search([('secret_code', '=', verification_number)], limit=1)
        )
        if not contact_verification:
            return request.render('mailing_verification.verification_failed')
        if contact_verification.mailing_contact_id:
            contact_verification.mailing_contact_id.is_verified = True
        if contact_verification.partner_id:
            contact_verification.partner_id.is_verified = True
        if contact_verification.partner_id.mailing_contact_ids:
            contact_verification.partner_id.mailing_contact_ids.is_verified = True
        contact_verification.unlink()
        return request.render('mailing_verification.verification_success')
