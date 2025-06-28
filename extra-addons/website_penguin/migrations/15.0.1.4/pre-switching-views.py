# -*- coding: utf-8 -*-
import logging
from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    view_names = [
        'website.header_language_selector',
        'website.header_language_selector_flag',
    ]
    for view_name in view_names:
        view = env.ref(view_name, raise_if_not_found=False)
        if view:
            state = not view.active
            _logger.info('Switching to view with name %s ref id %d to state %s' %
                         (view_name, view.id, state))
            view.active = state
