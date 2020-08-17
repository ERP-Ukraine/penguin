import logging

from . import models

from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def set_inventory_availability_on_product_templates(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    _logger.info('Post init hook: set inventory_availability = "always" for all active product templates')
    product_ids = env['product.template'].search([])
    product_ids.write({'inventory_availability': 'always'})
    _logger.info('Post init hook: done, %s products processed', len(product_ids))
