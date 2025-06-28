# -*- coding: utf-8 -*-
# !/usr/bin/python3
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class GoogleShoppingInstance(models.Model):
    _name = "google.shopping.feed.instance"
    _inherit = ['image.mixin']
    _description = "Google Shopping Feed Instance - Creating country wise"

    name = fields.Char(string='Instance Name', required=True, help="Insert google shopping instance name")
    gs_account_id = fields.Many2one("google.shopping.feed.account", string="Shopping Account", help="Google account id")
    gs_company_id = fields.Many2one("res.company", related="gs_account_id.gs_company_id", store=True, string="Company",
                                    help="Company ID")
    country_id = fields.Many2one("res.country", "Country", help="Google Country")
    language = fields.Many2one("res.lang", "Language")
    pricelist = fields.Many2one("product.pricelist", string="Google Shop Pricelist", help="Product pricelist")
    offer_pricelist = fields.Many2one("product.pricelist", string="Google Shop Offer Pricelist", help="Product Offer Pricelist")
    state = fields.Selection([
        ('new', 'New'),
        ('confirmed', 'Confirmed')
    ], default='new', help="State")
    product_price_with_tax = fields.Boolean("Product Price with Tax",
                                            help="If you want to export product price with excluded tax price then \
                                            enable this option.")
    product_price_account_tax = fields.Many2one("account.tax", 
                                                "Product Price Account Tax", help="Select tax product product price.")

    @api.constrains('gs_account_id', 'country_id')
    def _check_duplicate_instance(self):
        google_shopping_instances = self.search(
            [('gs_account_id', '=', self.gs_account_id.id), ('country_id', '=', self.country_id.id)])
        if google_shopping_instances and len(google_shopping_instances) > 1:
            raise ValidationError(
                _('You can not create same duplicate Google Shopping Instance with same Google Shopping Account and Country.'))
        return True

    def confirm_gsf_instance(self):
        for instance in self:
            if instance.gs_account_id.state != "confirmed":
                raise UserError(
                    _("First you have to confirm Shopping Account after you can confirm Shopping Instances."))
            else:
                instance.state = "confirmed"

    def reset_new_gsf_instance(self):
        for instance in self:
            instance.state = 'new'
