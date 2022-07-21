import logging
from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)

def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})

    DE_code = 'de_CH'
    available_lang_codes = [code for code, _, name, *_ in env['res.lang'].get_available()]
    if DE_code in available_lang_codes:
        lang_wizard = env['base.language.install'].create({'lang': 'de_CH', 'overwrite': True, 'state': 'done'})
        lang_wizard.lang_install()
