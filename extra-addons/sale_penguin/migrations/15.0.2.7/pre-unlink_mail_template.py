import logging
from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    view = env.ref('sale_penguin.mail_template_sale_confirmation')
    if view:
        _logger.info('Unlinking mail template with id %s', view.id)
        view.unlink()
