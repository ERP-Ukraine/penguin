from odoo import fields, models, api, _
import requests
import json
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    jfsku = fields.Char(string='JFSKU', copy=False)
    merchant_sku = fields.Char(string='Merchant SKU', copy=False)
    origin_country_id = fields.Many2one('res.country', string='Origin Country')
    manufacturer = fields.Char()
    net_weight = fields.Float()
    mpn = fields.Char(string='Manufacturer Part Number', copy=False)
    ean = fields.Char(string='EAN', copy=False)
    isbn = fields.Char(string='ISBN', copy=False)
    upc = fields.Char(string='UPC', copy=False)
    asin = fields.Char(string='ASIN', copy=False)
    un_number = fields.Char(string='Un Number', copy=False)
    hazard_identifier = fields.Char(copy=False)
    taric = fields.Char(copy=False)
    fnsku = fields.Char(copy=False)
    is_batch = fields.Boolean()
    is_divisible = fields.Boolean()
    is_best_before = fields.Boolean()
    width = fields.Float()
    length = fields.Float()
    height = fields.Float()
    authorized_partner_ids = fields.Many2many('res.partner', 'product_template_auth_partner_rel', 'pt_id', 'partner_id', string='Authorized Fulfillers')

    def get_ffn_headers(self):
        company = self.env.company
        return {
            "Authorization": company.ffn_token,
            "Accept": "application/json",
            "content-type": "application/json",
        }

    def sync_ffn_product(self):
        if not self.merchant_sku:
            raise ValidationError(_("please add merchant SKU"))
        data = {
            "name": self.name,
            "merchantSku": self.merchant_sku,
            "originCountry": self.origin_country_id.code or None,
            "manufacturer": self.manufacturer,
            "weight": self.weight,
            "netWeight": self.net_weight,
            "note": self.description,
            "identifier": {
                "mpn": {
                    "manufacturer": self.manufacturer,
                    "partNumber": self.mpn
                },
                "ean": self.ean,
                "isbn": self.isbn,
                "upc": self.upc,
                "asin": self.asin
            },
            "specifications": {
                "unNumber": self.un_number,
                "hazardIdentifier": self.hazard_identifier,
                "taric": self.taric,
                "fnsku": self.fnsku,
                "isBatch": self.is_batch,
                "isDivisible": self.is_divisible,
                "isBestBefore": self.is_best_before,
                "isSerialNumber": True if self.tracking == 'serial' else False,
                "isBillOfMaterials": False,
                "billOfMaterialsComponents": [],
                "isPackaging": False
            },
            "dimensions": {
                "width": self.width,
                "length": self.length,
                "height": self.height
            },
            "netRetailPrice": {
                "amount": self.list_price,
                "currency": self.currency_id.name
            },
        }
        if self.jfsku:
            if self.env.company.ffn_env_type == 'production':
                url = f"https://ffn.api.jtl-software.com/api/v1/merchant/products/{self.jfsku}"
            else:
                url = f"https://ffn-sbx.api.jtl-software.com/api/v1/merchant/products/{self.jfsku}"
            response = requests.patch(url, data=json.dumps(data), headers=self.get_ffn_headers())
            if response.status_code == 204:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'target': 'new',
                    'params': {
                        'title': 'Success',
                        'message': _("Product Synced Successfully!"),
                        'type': 'success',
                        'sticky': False,
                        'next': {'type': 'ir.actions.act_window_close'},
                    }
                }
        else:
            if self.env.company.ffn_env_type == 'production':
                url = "https://ffn.api.jtl-software.com/api/v1/merchant/products"
            else:
                url = "https://ffn-sbx.api.jtl-software.com/api/v1/merchant/products"
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
                self.jfsku = data['jfsku']
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'target': 'new',
                    'params': {
                        'title': 'Success',
                        'message': _("Product Synced Successfully!"),
                        'type': 'success',
                        'sticky': False,
                        'next': {'type': 'ir.actions.act_window_close'},
                    }
                }

    def delete_ffn_product(self):
        if self.jfsku:
            if self.env.company.ffn_env_type == 'production':
                url = f"https://ffn.api.jtl-software.com/api/v1/merchant/products/{self.jfsku}"
            else:
                url = f"https://ffn-sbx.api.jtl-software.com/api/v1/merchant/products/{self.jfsku}"
            response = requests.delete(url, headers=self.get_ffn_headers())
            if response.status_code == 204:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'target': 'new',
                    'params': {
                        'title': 'Success',
                        'message': _("Product removed Successfully!"),
                        'type': 'success',
                        'sticky': False,
                        'next': {'type': 'ir.actions.act_window_close'},
                    }
                }
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

    def authorize_ffn_product(self):
        return {
            'name': 'Grant a fulfiller access to a product',
            'type': 'ir.actions.act_window',
            'res_model': 'ffn.authorize',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_product_id': self.id,
                'default_show_grant_all': False,
            }
        }

    def get_ffn_stock(self):
        if self.env.company.ffn_env_type == 'production':
            url = f"https://ffn.api.jtl-software.com/api/v1/merchant/stocks/{self.jfsku}"
        else:
            url = f"https://ffn-sbx.api.jtl-software.com/api/v1/merchant/stocks/{self.jfsku}"
        response = requests.get(url, headers=self.get_ffn_headers())
        if response.status_code == 200 and response.content:
            data = json.loads(response.content.decode())
            if data['warehouses']:
                for warehouse in data['warehouses']:
                    warehouse_id = self.env['stock.warehouse'].search([('ffn_id', '=', warehouse['warehouseId'])])
                    if warehouse_id:
                        available_qty = sum(self.env['stock.quant'].search([
                            ('product_id', '=', self.product_variant_id.id), ('location_id', '=', warehouse_id.lot_stock_id.id),
                        ]).mapped('quantity'))
                        if available_qty != warehouse['stockLevel']:
                            quant = self.env['stock.quant'].create({
                                'location_id': warehouse_id.lot_stock_id.id,
                                'product_id': self.product_variant_id.id,
                                'inventory_quantity': warehouse['stockLevel'],
                            })
                            quant.action_apply_inventory()
