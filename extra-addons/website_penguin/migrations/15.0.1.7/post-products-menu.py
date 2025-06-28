import logging
from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    urls = ['/shell', '/insulation', '/fleece', '/merino', '/accessoires']
    products_child_menus = env['website.menu'].search([('url', 'in', urls)])
    products_menu = env['website.menu'].search([('url', '=', '/products'), ('website_id', '!=', False)], limit=1)
    if products_menu and products_child_menus:
        products_child_menus.parent_id = products_menu
        _logger.info('%d child ids added to "Products" menu', len(products_child_menus))
