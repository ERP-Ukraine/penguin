# -*- coding: utf-8 -*-
import logging

from . import controllers
from . import models
from . import report

from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def set_inventory_availability_on_product_templates(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    _logger.info('Post init hook: set show_availability = True for all active product templates')
    product_ids = env['product.template'].search([])
    product_ids.write({'show_availability': True, 'available_threshold': 2})
    _logger.info('Post init hook: done, %s products processed', len(product_ids))
