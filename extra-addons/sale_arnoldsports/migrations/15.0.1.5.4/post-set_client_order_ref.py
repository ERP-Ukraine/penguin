import logging

from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)

def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    domain = [('arnold_report_id', '!=', False), ('client_order_ref', 'in', ['', False])]
    sale_order_ids = env['sale.order'].search(domain)
    if sale_order_ids:
        _logger.info('%d arnoldsports orders found without client reference', len(sale_order_ids))
        regex = env['sale.order.arnold.report']._regex
        for so_id in sale_order_ids:
            client_order_ref = regex.search(so_id.arnold_report_id.name)
            so_id.client_order_ref = client_order_ref and client_order_ref.group() or ''

