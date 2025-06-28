# -*- coding: utf-8 -*-
import logging
from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    view_names = ['website_sale_penguin.website_product_template_form_view',
                  'website_sale_penguin.penguin_frontend_layout']
    for view_name in view_names:
        view = env.ref(view_name, raise_if_not_found=False)
        if view:
            _logger.info('Unlinking view with id %d' % view.id)
            view.unlink()

    views = env['ir.ui.view'].search([('key', '=', 'website_sale_penguin.penguin_product')])
    if views:
        _logger.info('Unlinking penguin_product views with ids %s' % view.ids)
        views.unlink()
