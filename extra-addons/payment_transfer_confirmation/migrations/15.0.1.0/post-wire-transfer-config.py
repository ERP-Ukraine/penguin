# -*- coding: utf-8 -*-
import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    _logger.info('Wire Transfer acquirers: setting authorization support')
    wire_acquirers = env['payment.acquirer'].search([('provider', '=', 'transfer')])
    if wire_acquirers:
        wire_acquirers.write({'support_authorization': True})
        _logger.info('Wire Transfer acquirers: set %d acquirers', len(wire_acquirers))
