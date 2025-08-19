from odoo import fields, models, api
import requests
import json


class FFNConnector(models.TransientModel):
    _name = 'ffn.connector'
    _description = 'FFN Connector'

    fulfillers = fields.Boolean()
    products = fields.Boolean()
    shipping_methods = fields.Boolean()
    warehouses = fields.Boolean()

    def button_connect(self):
        if self.fulfillers:
            self.get_fulfillers()
        if self.products:
            self.get_products()
        if self.shipping_methods:
            self.get_shipping_methods()
        if self.warehouses:
            self.get_warehouses()
        return {
            'name': 'FFN Connector',
            'type': 'ir.actions.act_window',
            'res_model': 'ffn.connector',
            'view_mode': 'form',
            'target': 'new',
            'res_id': self.id
        }

    def get_headers(self):
        company = self.env.company
        return {
            "Authorization": company.ffn_token,
        }

    def get_country(self, code):
        country_id = False
        if code:
            country = self.env['res.country'].search([('code', '=', code)])
            if country:
                country_id = country.id
        return country_id

    def get_currency(self, code):
        currency_id = False
        if code:
            currency = self.env['res.currency'].search([('name', '=', code)])
            if currency:
                currency_id = currency.id
        return currency_id

    def get_fulfillers(self):
        company = self.env.company
        if company.ffn_env_type == 'production':
            url = "https://ffn.api.jtl-software.com/api/v1/merchant/fulfillers"
        else:
            url = "https://ffn-sbx.api.jtl-software.com/api/v1/merchant/fulfillers"
        response = requests.get(url, headers=self.get_headers())
        if response.status_code == 200 and response.content:
            data = json.loads(response.content.decode())
            if data['items']:
                for item in data['items']:
                    address = item['address']
                    # name
                    name = address['firstname']
                    if address.get("lastname", False):
                        name += ' '
                        name += address['lastname']
                    # country
                    country_id = self.get_country(address['country'])
                    fulfiller_id = self.env['res.partner'].search([('ffn_id', '=', item['userId'])])
                    if fulfiller_id:
                        fulfiller_id.write({
                            'ffn_id': item['userId'],
                            'ffn_is_active': item['isActive'],
                            'name': name,
                            'street': address['street'],
                            'city': address['city'],
                            'zip': address['zip'],
                            'country_id': country_id,
                            'email': address['email'],
                            'phone': address['phone'],
                        })
                    else:
                        self.env['res.partner'].create({
                            'ffn_id': item['userId'],
                            'ffn_is_active': item['isActive'],
                            'name': name,
                            'street': address['street'],
                            'city': address['city'],
                            'zip': address['zip'],
                            'country_id': country_id,
                            'email': address['email'],
                            'phone': address['phone'],
                        })

    def get_products(self):
        if self.env.company.ffn_env_type == 'production':
            url = "https://ffn.api.jtl-software.com/api/v1/merchant/products"
        else:
            url = "https://ffn-sbx.api.jtl-software.com/api/v1/merchant/products"
        response = requests.get(url, headers=self.get_headers())
        if response.status_code == 200 and response.content:
            data = json.loads(response.content.decode())
            if data['items']:
                for item in data['items']:
                    product_id = self.env['product.template'].search([('jfsku', '=', item['jfsku'])])
                    if not product_id:
                        identifier = item['identifier']
                        mpn = False
                        specifications = item['specifications']
                        width = 0
                        length = 0
                        height = 0
                        amount = 0
                        currency_id = False
                        if item.get('dimensions', False):
                            dimensions = item['dimensions']
                            width = dimensions['width']
                            length = dimensions['length']
                            height = dimensions['height']
                        if identifier.get('mpn', False):
                            if identifier['mpn'].get('partNumber', False):
                                mpn = identifier['mpn']['partNumber']
                        if item.get('netRetailPrice', False):
                            if item['netRetailPrice'].get('currency', False):
                                currency_id = self.get_currency(item['netRetailPrice']['currency'])
                            if item['netRetailPrice'].get('amount', False):
                                amount = item['netRetailPrice']['amount']
                        # create product
                        self.env['product.template'].create({
                            'name': item['name'],
                            'jfsku': item['jfsku'],
                            'type': 'consu',
                            'is_storable': True,
                            'merchant_sku': item['merchantSku'],
                            'origin_country_id': self.get_country(item['originCountry']) if item.get('originCountry', False) else False,
                            'manufacturer': item.get('manufacturer', False),
                            'weight': item.get('weight', False),
                            'net_weight': item.get('netWeight', False),
                            'description': item['note'],
                            'mpn': mpn,
                            'ean': identifier.get('ean', False),
                            'isbn': identifier.get('isbn', False),
                            'upc': identifier.get('upc', False),
                            'asin': identifier.get('asin', False),
                            'un_number': specifications.get('unNumber', False),
                            'hazard_identifier': specifications.get('hazardIdentifier', False),
                            'taric': specifications.get('taric', False),
                            'fnsku': specifications.get('fnsku', False),
                            'is_batch': specifications.get('isBatch', False),
                            'is_divisible': specifications.get('isDivisible', False),
                            'is_best_before': specifications.get('isBestBefore', False),
                            'tracking': 'serial' if specifications.get('isSerialNumber', False) else 'none',
                            'width': width,
                            'length': length,
                            'height': height,
                            'list_price': amount,
                            'currency_id': currency_id,
                        })

    def get_shipping_methods(self):
        if self.env.company.ffn_env_type == 'production':
            url = "https://ffn.api.jtl-software.com/api/v1/merchant/shippingmethods"
        else:
            url = "https://ffn-sbx.api.jtl-software.com/api/v1/merchant/shippingmethods"
        response = requests.get(url, headers=self.get_headers())
        if response.status_code == 200 and response.content:
            data = json.loads(response.content.decode())
            if data['items']:
                for item in data['items']:
                    shipping_method_id = self.env['delivery.carrier'].search([('ffn_id', '=', item['shippingMethodId'])])
                    partner_id = self.env['res.partner'].search([('ffn_id', '=', item['fulfillerId'])])
                    if shipping_method_id:
                        shipping_method_id.write({
                            'ffn_id': item['shippingMethodId'],
                            'name': item['name'],
                            'partner_id': partner_id.id if partner_id else False,
                            'product_id': self.env.ref('delivery.product_product_delivery').id
                        })
                    else:
                        self.env['delivery.carrier'].create({
                            'ffn_id': item['shippingMethodId'],
                            'name': item['name'],
                            'partner_id': partner_id.id if partner_id else False,
                            'product_id': self.env.ref('delivery.product_product_delivery').id
                        })

    def get_warehouses(self):
        if self.env.company.ffn_env_type == 'production':
            url = "https://ffn.api.jtl-software.com/api/v1/merchant/warehouses"
        else:
            url = "https://ffn-sbx.api.jtl-software.com/api/v1/merchant/warehouses"
        response = requests.get(url, headers=self.get_headers())
        if response.status_code == 200 and response.content:
            data = json.loads(response.content.decode())
            if data['items']:
                for item in data['items']:
                    warehouse_id = self.env['stock.warehouse'].search([('ffn_id', '=', item['warehouseId'])])
                    partner_id = self.env['res.partner'].search([('ffn_id', '=', item['fulfillerId'])])
                    carriers = []
                    for carrier in item['shippingMethodIds']:
                        carrier_id = self.env['delivery.carrier'].search([('ffn_id', '=', carrier)])
                        if carrier_id:
                            carriers.append(carrier_id.id)
                    if warehouse_id:
                        warehouse_id.write({
                            'ffn_id': item['warehouseId'],
                            'partner_id': partner_id.id if partner_id else False,
                            'delivery_carrier_ids': [(6, 0, carriers)]
                        })
                    else:
                        self.env['stock.warehouse'].create({
                            'ffn_id': item['warehouseId'],
                            'name': item['name'],
                            'code': item['warehouseId'][:2] + item['warehouseId'][-3:],
                            'partner_id': partner_id.id if partner_id else False,
                            'delivery_carrier_ids': [(6, 0, carriers)]
                        })
