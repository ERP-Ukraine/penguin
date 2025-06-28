import logging

from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    _logger.info('Migration to version 13.0.1.1 begin!')

    _logger.info('Move value from Customer Group to Industry field')
    env = api.Environment(cr, SUPERUSER_ID, {})
    partner_ids = env['res.partner'].search([('country_ref', '!=', False)])
    _logger.info('%s customer(s) selected', len(partner_ids))
    for p in partner_ids:
        industry_id = env.ref('base_penguin.industry_{}'.format(p.country_ref), False)
        if industry_id:
            p.industry_id = industry_id.id

    _logger.info('Migration to version 13.0.1.1 successfully completed')

