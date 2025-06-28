# -*- coding: utf-8 -*-
import logging
from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    _logger.info('Set show_availability = True for all active product templates')
    product_ids = env['product.template'].search([])
    product_ids.write({'show_availability': True, 'available_threshold': 2})
    _logger.info('Done, %s products processed', len(product_ids))
