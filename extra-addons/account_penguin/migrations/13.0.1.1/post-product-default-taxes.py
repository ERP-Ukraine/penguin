import logging

from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    _logger.info('Migration to version 13.0.1.1 begin!')

    _logger.info('Set default taxes for selected products')
    env = api.Environment(cr, SUPERUSER_ID, {})
    product_ids = env['product.template'].search([])
    _logger.info('%s product(s) selected', len(product_ids))
    account_sale_tax_ids = env['res.company'].search([]).mapped('account_sale_tax_id')
    for p in product_ids:
        p.taxes_id = [(6, 0, account_sale_tax_ids.ids)]

    _logger.info('Migration to version 13.0.1.1 successfully completed')

