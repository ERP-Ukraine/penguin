# -*- coding: utf-8 -*-
import logging
from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    view_names = ['payment_wallee.assets_frontend',
                  'payment_wallee.payment_tokens_list_wallee',
                  'payment_wallee.wallee_form',
                  ]
    for view_name in view_names:
        view = env.ref(view_name, raise_if_not_found=False)
        if view:
            _logger.info('Unlinking view with id %d' % view.id)
            view.unlink()
