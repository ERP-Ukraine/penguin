# -*- coding: utf-8 -*-
import logging
from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    view_names = ['sale_coupon.sale_coupon_program_view_promo_program_form_penguin',
                  'sale_coupon.sale_coupon_program_view_form_common',
                  'sale_coupon.sale_coupon_view_form_penguin',
                  'sale_coupon_penguin.report_coupon_penguin']
    for view_name in view_names:
        view = env.ref(view_name, raise_if_not_found=False)
        if view:
            _logger.info('Unlinking view with id %d' % view.id)
            view.unlink()
