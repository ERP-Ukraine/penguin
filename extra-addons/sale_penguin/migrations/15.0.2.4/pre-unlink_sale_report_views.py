import logging
import pprint

from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)

def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    view_names = [
        'sale_penguin.report_saleorder_document_pricelist',
        'sale_penguin.report_saleorder_document_title',
        'sale_penguin.report_saleorder_document_custom_main_table',
    ]
    views = env['ir.ui.view'].search([('key', 'in', view_names)])
    if views:
        log_message = 'Unlinking views: %s' % list(zip(views.mapped('key'), views.ids))
        _logger.info(pprint.pformat(log_message))
        views.unlink()
