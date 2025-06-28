import logging

from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    domain = [('industry_id', '=', False),
              ('country_id', '!=', False)]
    switzerland = env.ref('base.ch')
    swiss_industry = env.ref('base_penguin.industry_online_cust_swiss')
    europe_industry = env.ref('base_penguin.industry_online_cust_europe')
    partners = env['res.partner'].search(domain)
    for p in partners:
        p.industry_id = swiss_industry if p.country_id == switzerland else europe_industry
    _logger.info('Set industry on %s partners', len(partners))
