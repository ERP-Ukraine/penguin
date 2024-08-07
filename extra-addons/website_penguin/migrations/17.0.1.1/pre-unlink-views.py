# -*- coding: utf-8 -*-
import logging
from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    view_names = [
        'website.aboutus',
        'website.accessoires',
        'website.ambassador',
        'website.care',
        'website.fleecemidlayer',
        'website.insulationmidlayer',
        'website.penguinmovie',
        'website_penguin.philosophy',
        'website.shelllayer',
        'website.stores',
        'website.toursandevents'
    ]
    for view_name in view_names:
        view = env.ref(view_name, raise_if_not_found=False)
        if view:
            _logger.info('Unlinking view with id %d' % view.id)
            view.unlink()
