# -*- coding: utf-8 -*-
import logging
from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    urls = ['/philosophy', '/penguinmovie', '/penguincare', '/stores', '/ambassador', '/customerservice', '/toursandevents']
    about_child_menus = env['website.menu'].search([('url', 'in', urls)])
    about_menu = env['website.menu'].search([('url', '=', '/about'), ('website_id', '!=', False)], limit=1)
    if about_menu and about_child_menus:
        about_child_menus.parent_id = about_menu
        _logger.info('%d child ids added to "About" menu', len(about_child_menus))
