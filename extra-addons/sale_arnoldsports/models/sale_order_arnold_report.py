import base64
import csv
import io
import logging
import re

from dateutil import parser
from odoo import _, api, fields, models
from odoo.tests.common import Form

_logger = logging.getLogger(__name__)


class SaleOrderArnoldReport(models.Model):
    _name = 'sale.order.arnold.report'
    _inherit = ['mail.thread']
    _description = 'Order Report from ArnoldSports sent via email'

    _regex = re.compile(r'(RG\d{7})')

    active = fields.Boolean(default=True)
    name = fields.Char(default='Arnold Order Report', readonly=True)
    order_ids = fields.One2many(
        'sale.order',
        'arnold_report_id',
        string='Sale Orders',
        readonly=True)

    @api.model
    def _cron_create_orders(self, limit=1):
        if not self.env['ir.config_parameter'].sudo().get_param(
                'sale_arnoldsports.generate_arnold_orders'):
            return
        reports = self.search([('active', '=', True)], limit=limit)
        for report in reports:
            report_lines = []
            attachments = self.env['ir.attachment'].search([
                ('res_id', 'in', report.ids),
                ('res_model', '=', self._name)])
            for attachment in attachments:
                if not attachment.name.lower().endswith('.csv'):
                    continue
                bin_data = base64.b64decode(attachment.datas)
                for line in csv.DictReader(io.StringIO(bin_data.decode('utf-8')), delimiter=';'):
                    report_lines.append(line)
            if report_lines:
                success = self._create_order_from_lines(lines=report_lines, report=report, report_name=report.name)
                report.active = not success
            self.env.cr.commit()

    @api.model
    def _create_order_from_lines(self, lines=None, report=None, report_name=None):
        partner_id = int(self.env['ir.config_parameter'].sudo().get_param(
            'sale_arnoldsports.arnold_partner_id'))
        if not partner_id:
            _logger.warning('ARNOLD SPORTS partner not configured')
            return False
        warehouse_id = int(self.env['ir.config_parameter'].sudo().get_param(
            'sale_arnoldsports.arnold_warehouse_id'))
        if not warehouse_id:
            _logger.warning('ARNOLD SPORTS warehouse not configured')
            return False
        fpos_id = int(self.env['ir.config_parameter'].sudo().get_param(
            'sale_arnoldsports.arnold_fpos_id'))
        if not fpos_id:
            _logger.warning('ARNOLD SPORTS fiscal position not configured')
            return False
        discount = float(self.env['ir.config_parameter'].sudo().get_param(
            'sale_arnoldsports.discount', '26.0'))
        partner = self.env['res.partner'].browse(partner_id)
        partner_user = partner.user_id or partner.commercial_partner_id.user_id
        fiscal_position = self.env['account.fiscal.position'].browse(fpos_id)
        warehouse = self.env['stock.warehouse'].browse(warehouse_id)
        lines_by_date = {}
        for line in lines:
            if not line['date']:
                # skip empty rows
                continue
            if line['date'] not in lines_by_date:
                lines_by_date[line['date']] = [line]
            else:
                lines_by_date[line['date']].append(line)
        for order_date in lines_by_date:
            customers = []
            order_dt = parser.parse(order_date, dayfirst=True)
            so_form = Form(self.env['sale.order'].with_context(not_self_saleperson=True))
            client_order_ref = self._regex.search(report_name)
            so_form.client_order_ref = client_order_ref and client_order_ref.group() or ''
            so_form.partner_id = partner
            so_form.fiscal_position_id = fiscal_position
            so_form.user_id = partner_user
            so_form.arnold_report_id = report
            so_form.commitment_date = order_dt
            so_form.date_order = order_dt
            so_form.warehouse_id = warehouse
            for line in lines_by_date[order_date]:
                if line['customer'] not in customers:
                    customers.append(line['customer'])
                article = line['article']
                if article.startswith('PN-'):
                    article = article[3:]
                product = self.env['product.product'].search([('default_code', '=', article)],
                                                             limit=1)
                if not product:
                    _logger.warning('[%s] Product with article %s not found', order_date, article)
                    report.message_post(body=_('Product with article %s not found') % article)
                    return False
                with so_form.order_line.new() as line_form:
                    qty = float(line['quantity'].strip().replace(',', '.'))
                    price_unit = (float(line['hek'].strip().replace(',', '.'))
                                  - float(line['discount_eur'].strip().replace(',', '.')))
                    line_form.product_id = product
                    line_form.product_uom_qty = qty
                    line_form.price_unit = price_unit
                    line_form.discount = discount
            so_form.origin = _('Customers: %s') % ', '.join(customers)
            so = so_form.save()
            so.action_confirm()
            so.date_order = order_dt
        return True
