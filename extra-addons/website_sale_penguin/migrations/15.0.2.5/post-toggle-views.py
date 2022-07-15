# -*- coding: utf-8 -*-
import logging
from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    view_names = ['website_sale.product_share_buttons']
    for view_name in view_names:
        view = env.ref(view_name, raise_if_not_found=False)
        if view:
            _logger.info('Toggling active state for view with id %d to %s' % (view.id, not view.active))
            view.active = not view.active
