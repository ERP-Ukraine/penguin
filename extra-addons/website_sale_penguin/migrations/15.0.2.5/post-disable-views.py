# -*- coding: utf-8 -*-
import logging
from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    view_names = ['website_sale.add_grid_or_list_option',
                  'website_sale.sort',
                  'website_sale.products_breadcrumb']
    for view_name in view_names:
        view = env.ref(view_name, raise_if_not_found=False)
        if view:
            _logger.info('Disabling view with id %d' % view.id)
            view.active = False
