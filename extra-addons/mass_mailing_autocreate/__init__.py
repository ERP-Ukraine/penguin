# -*- coding: utf-8 -*-
import logging
from . import models
from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)

def add_contacts_to_mailing_list(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    _logger.info('Post init hook: add all contacts to mailing list')
    partner_fields = env['res.partner'].search_read([('email', '!=', False)], ['name', 'email'])
    emails_list = env['mailing.contact'].search_read([], ['email'])
    emails = {el['email'] for el in emails_list}
    list_id = env.company.contacts_mass_mailing_list.id
    if not list_id:
        return
    vals_list = [{'name': el['name'], 'email': el['email'],
                  'list_ids': [(4, list_id)]} for el in partner_fields if el['email'] not in emails]
    contacts = env['mailing.contact'].create(vals_list)
    _logger.info('Post init hook: done, %s contacts added', len(contacts))
