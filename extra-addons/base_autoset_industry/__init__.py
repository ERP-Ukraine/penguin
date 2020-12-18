# -*- coding: utf-8 -*-
import logging
from . import models
from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)

def set_default_industry_field(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    _logger.info('Post init hook: set default contact industry field')
    users = env['res.users'].search([('share', '=', True)])
    done_users = users._set_industry_field()
    _logger.info('Post init hook: done, %s contacts updated', len(done_users))
