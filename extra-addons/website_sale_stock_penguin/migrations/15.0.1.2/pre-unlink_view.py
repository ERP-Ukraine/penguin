import logging

from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)

def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    view = env.ref('website_sale_stock_penguin.report_delivery_document_with_comment', raise_if_not_found=False)
    if view:
        _logger.info('Unlinking view with id %d' % view.id)
        view.unlink()
