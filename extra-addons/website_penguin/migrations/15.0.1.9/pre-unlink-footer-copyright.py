import logging
from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    view = env.ref('website_penguin.footer_copyright_company_name',
                    raise_if_not_found=False)
    if view:
        view.unlink()

