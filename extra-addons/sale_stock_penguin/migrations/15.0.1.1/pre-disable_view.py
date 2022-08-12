import logging

from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)

def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    view = env.ref('sale_stock.report_delivery_document_inherit_sale_stock', raise_if_not_found=False)
    if view:
        _logger.info('Disabling view with id %d' % view.id)
        view.active = False
