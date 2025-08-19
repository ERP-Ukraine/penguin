from odoo import fields, models, api, _
import requests
import json
from odoo.exceptions import ValidationError
from dateutil import parser
from datetime import datetime


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    ffn_id = fields.Char(string='FFN ID', copy=False)
    fulfiller_state = fields.Selection(selection=[
        ('Preparation', 'Preparation'),
        ('Pending', 'Pending'),
        ('Acknowledged', 'Acknowledged'),
        ('Pickprocess', 'Pickprocess'),
        ('Locked', 'Locked'),
        ('PartiallyShipped', 'PartiallyShipped'),
        ('Shipped', 'Shipped'),
        ('PartiallyCanceled', 'PartiallyCanceled'),
        ('Canceled', 'Canceled'),
    ], string='Fulfiller Status', copy=False)
    fsnn = fields.Char(string='Fulfiller Shipping Notification Number', copy=False)
    osni = fields.Char(string='Outbound Shipping Notification Id', copy=False)
    package_ids = fields.One2many('sale.order.package', 'order_id')

    def get_ffn_headers(self):
        company = self.env.company
        return {
            "Authorization": company.ffn_token,
            "Accept": "application/json",
            "content-type": "application/json",
        }

    def sync_ffn_outbound(self):
        if not self.warehouse_id.ffn_id:
            raise ValidationError(_("please select ffn warehouse"))
        data = {
            "outboundId": f"MERC02AXEV{self.id}",
            "merchantOutboundNumber": self.name,
            "warehouseId": self.warehouse_id.ffn_id,
            "currency": self.currency_id.name,
            "shippingType": "Standard",
            "shippingAddress": self.prepare_ffn_shipping_address(),
            "orderValue": self.amount_total,
            "items": self.prepare_ffn_so_lines(),
            "note": self.note,
        }
        if self.env.company.ffn_env_type == 'production':
            url = "https://ffn.api.jtl-software.com/api/v1/merchant/outbounds"
        else:
            url = "https://ffn-sbx.api.jtl-software.com/api/v1/merchant/outbounds"
        response = requests.post(url, data=json.dumps(data), headers=self.get_ffn_headers())
        if response.content:
            data = json.loads(response.content.decode())
            if data.get("errorMessages", False):
                if data['errorMessages'][0]['message']:
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'target': 'new',
                        'params': {
                            'title': data['errorMessages'][0]['target'] if data['errorMessages'][0].get("target",
                                                                                                        False) else 'Error',
                            'message': data['errorMessages'][0]['message'],
                            'type': 'danger',
                            'sticky': False,
                            'next': {'type': 'ir.actions.act_window_close'},
                        }
                    }
            elif response.status_code == 201:
                self.ffn_id = data['outboundId']
                self.fulfiller_state = data['status']
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'target': 'new',
                    'params': {
                        'title': 'Success',
                        'message': _("Outbound Created Successfully!"),
                        'type': 'success',
                        'sticky': False,
                        'next': {'type': 'ir.actions.act_window_close'},
                    }
                }

    def prepare_ffn_so_lines(self):
        lines = []
        for line in self.order_line:
            lines.append({
                "outboundItemId": line.id,
                "jfsku": line.product_id.jfsku,
                "quantity": line.product_qty,
                "price": line.price_unit,
                "vat": line.price_tax
            })
        return lines

    def prepare_ffn_shipping_address(self):
        full_name = self.partner_id.name.split(" ")
        first_name = full_name[0] if len(full_name) > 0 else ""
        last_name = ' '.join(full_name[1:]) if len(full_name) > 1 else ""
        data = {
            "firstname": first_name,
            "lastname": last_name,
            "street": self.partner_id.street,
            "city": self.partner_id.city,
            "country": self.partner_id.country_id.code,
        }
        if self.partner_id.zip:
            data.update({"zip": self.partner_id.zip})
        if self.partner_id.email:
            data.update({"email": self.partner_id.email})
        if self.partner_id.phone:
            data.update({"phone": self.partner_id.phone})
        if self.partner_id.mobile:
            data.update({"mobile": self.partner_id.mobile})
        return data

    def get_ffn_outbound_state(self):
        if self.env.company.ffn_env_type == 'production':
            url = f"https://ffn.api.jtl-software.com/api/v1/merchant/outbounds/{self.name}"
        else:
            url = f"https://ffn-sbx.api.jtl-software.com/api/v1/merchant/outbounds/{self.name}"
        response = requests.get(url, headers=self.get_ffn_headers())
        if response.content:
            if response.status_code == 200 and response.content:
                data = json.loads(response.content.decode())
                old_state = self.fulfiller_state
                self.fulfiller_state = data['status']
                if self.fulfiller_state == 'Shipped' and old_state != 'Shipped':
                    if self.env.company.ffn_env_type == 'production':
                        url = f"https://ffn.api.jtl-software.com/api/v1/merchant/outbounds/{self.name}/shipping-notifications"
                    else:
                        url = f"https://ffn-sbx.api.jtl-software.com/api/v1/merchant/outbounds/{self.name}/shipping-notifications"
                    response = requests.get(url, headers=self.get_ffn_headers())
                    if response.content:
                        if response.status_code == 200 and response.content:
                            notifications = json.loads(response.content.decode())
                            for notification in notifications:
                                self.fsnn = notification.get('fulfillerShippingNotificationNumber', False)
                                self.osni = notification.get('outboundShippingNotificationId', False)
                                # items
                                for item in notification.get('items', []):
                                    line = self.order_line.filtered(lambda l: l.product_id.jfsku == item['jfsku'])
                                    if line:
                                        line = line[0]
                                        line.osnii = item['outboundShippingNotificationItemId']
                                # packages
                                package_vals = []
                                for package in notification.get('packages', []):
                                    tracking_id = False
                                    if len(package.get('identifier', [])) > 0:
                                        tracking_id = package['identifier'][0].get('value', False)
                                    # dt = datetime.strftime(parser.isoparse(package['shippingDate']), '%Y-%m-%d %H:%M:%S')
                                    shipping_method_id = self.env['delivery.carrier'].search([('ffn_id', '=', package.get('shippingMethodId', False))])
                                    package_vals.append((0, 0, {
                                        'freight_option': package.get('freightOption', False),
                                        'tracking_url': package.get('trackingUrl', False),
                                        'tracking_id': tracking_id,
                                        # 'shipping_date': dt,
                                        'shipping_method_id': shipping_method_id.id if shipping_method_id else False,
                                    }))
                                self.write({
                                    'package_ids': package_vals
                                })
                            self.action_confirm()
                            if self.picking_ids:
                                for picking in self.picking_ids:
                                    if picking.state == 'cancel':
                                        continue
                                    for move in picking.move_ids:
                                        move.quantity = move.product_qty
                                    picking._autoconfirm_picking()
                                    picking.button_validate()
                                    for move_line in picking.move_ids_without_package:
                                        move_line.quantity = move_line.product_uom_qty

                                    for mv_line in picking.move_ids.mapped('move_line_ids'):
                                        # if not mv_line.button_validate and mv_line.reserved_qty or mv_line.reserved_uom_qty:
                                        mv_line.quantity = mv_line.quantity_product_uom  # .reserved_qty or mv_line.reserved_uom_qty

                                    picking._action_done()

                            if not self.invoice_ids:
                                self._create_invoices()
                            if self.invoice_ids:
                                for invoice in self.invoice_ids:
                                    invoice.action_post()


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    osnii = fields.Char(string='Outbound Shipping Notification Item Id')


class SaleOrderPackage(models.Model):
    _name = 'sale.order.package'
    _description = 'Sale Order Package'

    order_id = fields.Many2one('sale.order')
    freight_option = fields.Char(string='Freight Option')
    tracking_url = fields.Char(string='Tracking URL')
    tracking_id = fields.Char(string='Tracking ID')
    shipping_date = fields.Datetime()
    shipping_method_id = fields.Many2one('delivery.carrier')
