import base64
import csv
import io
import logging

from dateutil import parser
from odoo import _, api, fields, models
from odoo.tests.common import Form

_logger = logging.getLogger(__name__)

try:
    from tnefparse.mapi import TNEFMAPI_Attribute
    from tnefparse.tnef import TNEF, TNEFAttachment, TNEFObject
except ImportError:
    _logger.warning('Arnold import disabled. Run pip3 install tnefparse')
    TNEF = None


class SaleOrderArnoldReport(models.Model):
    _name = 'sale.order.arnold.report'
    _inherit = ['mail.thread']
    _description = 'Order Report from ArnoldSports sent via email'

    active = fields.Boolean(default=True)
    name = fields.Char(default='Arnold Order Report', readonly=True)
    order_ids = fields.One2many(
        'sale.order',
        'arnold_report_id',
        string='Sale Orders',
        readonly=True)

    @api.model
    def _cron_create_orders(self):
        if not TNEF:
            return
        if not self.env['ir.config_parameter'].sudo().get_param(
                'sale_arnoldsports.generate_arnold_orders'):
            return
        reports = self.search([('active', '=', True)])
        for report in reports:
            report_lines = []
            attachments = self.env['ir.attachment'].search([
                ('res_id', 'in', report.ids),
                ('res_model', '=', self._name)])
            for attachment in attachments:
                if attachment.name.lower() != 'winmail.dat':
                    continue
                bin_data = base64.b64decode(attachment.datas)
                f = io.BytesIO(bin_data)
                t = TNEF(open(f).read(), do_checksum=True)
                for a in t.attachments:
                    if a.name.lower().endswith('.csv'):
                        with open(a.name, "r") as afp:
                            for line in csv.DictReader(afp):
                                report_lines.append(line)
            if report_lines:
                success = self._create_order_from_lines(lines=report_lines, report_id=report.id)
                report.active = not success
            self.env.cr.commit()

    @api.model
    def _create_order_from_lines(self, lines=None, report_id=None):
        partner_id = int(self.env['ir.config_parameter'].sudo().get_param(
            'sale_arnoldsports.arnold_partner_id'))
        if not partner_id:
            _logger.warning('ARNOLD SPORTS GmbH not found')
            return False
        partner = self.env['res.partner'].browse(partner_id)
        lines_by_date = {}
        for line in lines:
            if line['date'] not in lines_by_date:
                lines_by_date = [line]
            else:
                lines_by_date.append(line)
        for order_date in lines_by_date:
            customers = []
            order_dt = parser.parse(order_date, dayfirst=True)
            so_form = Form(self.env['sale.order'])
            so_form.partner_id = partner
            so_form.commitment_date = order_dt
            so_form.date_order = order_dt
            for line in lines_by_date[order_date]:
                if line['customer'] not in customers:
                    customers.append(line['customer'])
                product = self.env['product.product'].search([('ean', '=', line['ean'])], limit=1)
                if not product:
                    _logger.warning('[%s] Product with ean %s not found', order_date, line['ean'])
                    return False
                with so_form.order_line.new() as line_form:
                    qty = float(line['quantity'].strip())
                    unit_price = float(line['hek'].strip()) - float(line['discount_eur'].strip())
                    line_form.product_id = product
                    line_form.product_uom_qty = qty
                    line_form.unit_price = unit_price
            so_form.message_post(body=_('Customers: %s') % ', '.join(customers))
            so_form.action_confirm()
            so_form.date_order = order_dt
            so_form.save()
