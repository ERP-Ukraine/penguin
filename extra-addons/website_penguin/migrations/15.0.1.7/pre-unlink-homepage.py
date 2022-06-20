import logging
from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    views = env['ir.ui.view'].search([('key', '=', 'website.homepage')])
    if views:
        _logger.info('Unlinking homepage views with ids %s', views.ids)
        views.unlink()
    homepages = env['website.page'].search([('url', '=', '/')])
    if homepages:
        _logger.info('Unlinking homepages with ids %s', homepages.ids)
        homepages.unlink()
