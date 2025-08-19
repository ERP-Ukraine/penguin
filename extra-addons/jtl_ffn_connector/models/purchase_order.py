from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
import requests
import json


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    ffn_warehouse_id = fields.Many2one('stock.warehouse', string='FFN Warehouse')
    ffn_id = fields.Char(string='FFN ID', copy=False)
    fulfiller_state = fields.Char(string='Fulfiller Status', copy=False)

    @api.onchange('ffn_warehouse_id')
    def onchange_ffn_warehouse_id(self):
        if self.ffn_warehouse_id:
            self.picking_type_id = self.ffn_warehouse_id.in_type_id.id

    def get_ffn_headers(self):
        company = self.env.company
        return {
            "Authorization": company.ffn_token,
            "Accept": "application/json",
            "content-type": "application/json",
        }


    def sync_ffn_inbound(self):
        if not self.ffn_warehouse_id:
            raise ValidationError(_("please select ffn warehouse"))
        data = {
            "inboundId": f"MERC03INBND{self.id}",
            "items": self.prepare_po_lines(),
            "merchantInboundNumber": self.name,
            "warehouseId": self.ffn_warehouse_id.ffn_id,
            "note": self.notes,
            "purchaseOrderNumber": self.name,
            "externalInboundNumber": self.name
        }
        if self.env.company.ffn_env_type == 'production':
            url = "https://ffn.api.jtl-software.com/api/v1/merchant/inbounds"
        else:
            url = "https://ffn-sbx.api.jtl-software.com/api/v1/merchant/inbounds"
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
                            'title': data['errorMessages'][0]['target'] if data['errorMessages'][0].get("target", False) else 'Error',
                            'message': data['errorMessages'][0]['message'],
                            'type': 'danger',
                            'sticky': False,
                            'next': {'type': 'ir.actions.act_window_close'},
                        }
                    }
            elif response.status_code == 201:
                self.ffn_id = data['inboundId']
                self.fulfiller_state = data['status']
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'target': 'new',
                    'params': {
                        'title': 'Success',
                        'message': _("Inbound Created Successfully!"),
                        'type': 'success',
                        'sticky': False,
                        'next': {'type': 'ir.actions.act_window_close'},
                    }
                }

    def prepare_po_lines(self):
        lines = []
        for line in self.order_line:
            lines.append({
                "merchantSku": line.product_id.merchant_sku,
                "inboundItemId": line.id,
                "jfsku": line.product_id.jfsku,
                "quantity": line.product_qty,
                "supplierSku": line.product_id.default_code
            })
        return lines

    def get_ffn_inbound_state(self):
        if self.env.company.ffn_env_type == 'production':
            url = f"https://ffn.api.jtl-software.com/api/v1/merchant/inbounds/{self.name}"
        else:
            url = f"https://ffn-sbx.api.jtl-software.com/api/v1/merchant/inbounds/{self.name}"
        response = requests.get(url, headers=self.get_ffn_headers())
        if response.content:
            if response.status_code == 200 and response.content:
                data = json.loads(response.content.decode())
                self.fulfiller_state = data['status']
                if self.fulfiller_state == 'Receipted':
                    self.button_confirm()
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
                                mv_line.quantity = mv_line.quantity_product_uom
                            picking._action_done()


class PurchaseOrderLinr(models.Model):
    _inherit = 'purchase.order.line'

    ffn_note = fields.Char()
