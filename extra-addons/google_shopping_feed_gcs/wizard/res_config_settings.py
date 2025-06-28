# -*- coding: utf-8 -*-
#!/usr/bin/python3
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import models, fields, api
from odoo.http import request


class ResConfigGoogleShoppingFeedInstancetWizard(models.TransientModel):
    _name = "res.config.google.shopping.feed.instance.wizard"
    _description = "Instance Creation from Google Shopping Instance"

    name = fields.Char(string='Name', required=True, help="Insert google shopping account name")
    google_shop_account_id = fields.Many2one("google.shopping.feed.account", string="Shopping Account",
                                             help="Google account id")
    google_shop_country_id = fields.Many2one("res.country", "Country", help="Google Country")
    google_shop_language = fields.Many2one("res.lang", "Language")
    google_shop_pricelist = fields.Many2one("product.pricelist", help="Product pricelist")
    
    def create_google_shopping_instance(self):
        google_shopping_instance = self.env['google.shopping.feed.instance'].create({
            'name': self.name,
            'gs_account_id': self.google_shop_account_id.id,
            'country_id': self.google_shop_country_id.id,
            'language': self.google_shop_language.id,
            'pricelist': self.google_shop_pricelist.id,

        })
        return google_shopping_instance


class ResConfigGoogleShoppingFeedAccountWizard(models.TransientModel):
    _name = "res.config.google.shopping.feed.account.wizard"
    _description = "Account Creation from Google Shopping Setting"

    name = fields.Char(string='Name', required=True, help="Insert google shopping account name")
    gs_merchant_id = fields.Char("Merchant ID", help="Google merchant ID")
    gs_client_id = fields.Char("Client ID", help="Google client ID")
    gs_client_secret_key = fields.Char("Client Secret Key", help="Google client secret key")
    google_shop_company_id = fields.Many2one('res.company', string="Company")
    google_shop_stock_field = fields.Many2one('ir.model.fields', string='Stock Field')
    google_shop_warehouse_ids = fields.Many2many('stock.warehouse', "res_config_google_shopping_account_gcs_rel",
                                    string="Warehouses", help="Select warehouses")
    
    def create_google_shopping_account(self):
        google_shopping_account = self.env['google.shopping.feed.account'].create({
            'name': self.name,
            'gs_merchant_id': self.gs_merchant_id,
            'gs_client_id': self.gs_client_id,
            'gs_client_secret_key': self.gs_client_secret_key,
            'gs_company_id': self.google_shop_company_id.id,
            'warehouse_ids': self.google_shop_warehouse_ids.ids,
            'stock_field': self.google_shop_stock_field.id
        })
        return google_shopping_account


class ResConfigSettingsGoogleShoppingFeed(models.TransientModel):
    _inherit = 'res.config.settings'
    _description = "Google Shopping Setting"

    @api.model
    def create(self, vals):
        if not vals.get('google_shop_company_id'):
            vals.update({'google_shop_company_id': self.env.user.company_id.id})
        res = super(ResConfigSettingsGoogleShoppingFeed, self).create(vals)
        return res

    google_shop_company_id = fields.Many2one('res.company', string="Google Shopping Company")
    google_shop_account_id = fields.Many2one("google.shopping.feed.account", string="Shopping Account",
                                    help="Google account id")
    google_shop_warehouse_ids = fields.Many2many('stock.warehouse',
                                    domain="[('company_id', '=', google_shop_company_id)]",
                                    string="Warehouses", help="Select warehouses")
    google_shop_stock_field = fields.Many2one('ir.model.fields', string='Stock Field')
    google_shop_instance_id = fields.Many2one("google.shopping.feed.instance", string="Instance",
                                    help="Google instance  id")
    google_shop_country_id = fields.Many2one("res.country", "Country", help="Google Country")
    google_shop_language = fields.Many2one("res.lang", "Language")
    google_shop_pricelist = fields.Many2one("product.pricelist", string="Google Shop Pricelist",
                                    help="Product pricelist")
    google_shop_offer_pricelist = fields.Many2one("product.pricelist", string="Google Shop Offer Pricelist",
                                                  help="Product Offer pricelist")
    product_price_with_tax = fields.Boolean("Product Price with Tax",
                                            help="If you want to export product price with excluded tax price then \
                                            enable this option.")
    product_price_account_tax = fields.Many2one("account.tax",
                                                "Product Price Account Tax", help="Select tax product product price.")
    
    @api.onchange('google_shop_account_id')
    def onchange_google_shopping_account_id(self):
        values = {}
        if self.google_shop_account_id:
            request.session['google_shop_account_id'] = self.google_shop_account_id.id
            google_shop_account = self.env['google.shopping.feed.account'].browse(self.google_shop_account_id.id)
            
            values = self.onchange_google_shopping_instance_id()
            values['value']['google_shop_instance_id'] = False
            values['value']['google_shop_company_id'] = google_shop_account.gs_company_id and \
                google_shop_account.gs_company_id.id or False
            values['value']['google_shop_warehouse_ids'] = google_shop_account.warehouse_ids and \
                google_shop_account.warehouse_ids.ids or False 
            values['value']['google_shop_stock_field'] = google_shop_account.stock_field and \
                google_shop_account.stock_field.id or False
        else:
            values.update({'value': {'google_shop_instance_id': False}})
        return values
    
    @api.onchange('google_shop_instance_id')
    def onchange_google_shopping_instance_id(self):
        vals = {}
        instance = self.google_shop_instance_id
        if instance:
            vals['google_shop_country_id'] = instance.country_id and instance.country_id.id or False
            vals['google_shop_language'] = instance.language and instance.language.id or False
            vals['google_shop_pricelist'] = instance.pricelist and instance.pricelist.id or False
            vals['google_shop_offer_pricelist'] = instance.offer_pricelist and instance.offer_pricelist.id or False
            vals['product_price_with_tax'] = instance.product_price_with_tax
            vals['product_price_account_tax'] = instance.product_price_account_tax and \
                instance.product_price_account_tax.id or False
        return {'value': vals}
    
    def execute(self):
        values, vals = {}, {}
        instance = self.google_shop_instance_id or False
        res = super(ResConfigSettingsGoogleShoppingFeed, self).execute()
        if instance:
            values['country_id'] = self.google_shop_country_id and self.google_shop_country_id.id or False
            values['language'] = self.google_shop_language and self.google_shop_language.id or False
            values['pricelist'] = self.google_shop_pricelist and self.google_shop_pricelist.id or False
            values['offer_pricelist'] = self.google_shop_offer_pricelist and \
                self.google_shop_offer_pricelist.id or False
            values['product_price_with_tax'] = self.product_price_with_tax
            values['product_price_account_tax'] = self.product_price_account_tax and \
                self.product_price_account_tax.id or False 
            instance.write(values)
        if self.google_shop_account_id:
            vals['gs_company_id'] = self.google_shop_company_id and self.google_shop_company_id.id or False
            vals['warehouse_ids'] = self.google_shop_warehouse_ids and self.google_shop_warehouse_ids.ids \
                                                    or False
            vals['stock_field'] = self.google_shop_stock_field and self.google_shop_stock_field.id or False
            self.google_shop_account_id.write(vals)
        return res
            
    def create_more_google_shopping_instances(self):
        """
            Create new google shopping instances
            :return: Action or Error
        """
        action = self.env.ref('google_shopping_feed_gcs.res_config_google_shopping_instance_wizard_action', False)
        result = {}
        if action and action.read()[0]:
            result = action.read()[0]
        ctx = result.get('context', {}) and eval(result.get('context'))
        ctx.update({
            'default_google_shop_account_id': request.session['google_shop_account_id'],
        })
        result['context'] = ctx
        return result
