import logging
from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    domain = [('module', '=', 'sale'), ('name', '=', 'default_confirmation_template')]
    sale_confirmation_template = env['ir.model.data'].search(domain, limit=1)
    if sale_confirmation_template:
        sale_confirmation_template.noupdate = False
        _logger.info('Set noupdate set to False for mail template with id: %d', sale_confirmation_template.res_id)
