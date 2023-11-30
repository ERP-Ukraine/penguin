# -*- coding: utf-8 -*-
#!/usr/bin/python3
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging

from odoo import models, fields, api, _
from odoo.exceptions import Warning, UserError, ValidationError
from odoo.addons.google_shopping_feed_gcs.google_shopping_api.google_shopping_api import GoogleShoppingAPI

_logger = logging.getLogger(__name__)


class GoogleShoppingFeedAccount(models.Model):
    _name = "google.shopping.feed.account"
    _inherit = ['image.mixin']
    _description = "Google Shopping Feed Account"
    
    @api.depends('gs_instance_ids')
    def _compute_shopping_instances_ids(self):
        for shopping_account in self:
            shopping_account.gs_instances_count = len(shopping_account.gs_instance_ids)
    
    @api.depends('gs_website_id', "gs_website_domain")
    def get_and_set_authorized_redirect_uri(self):
        for shopping_account in self:
            if shopping_account.gs_website_domain:
                shopping_account.gs_authorized_redirect_uri = shopping_account.gs_website_domain + \
                    "/google_account/authentication2"
    
    def _compute_gsf_account_crons(self):
        gsf_account_crons = self.env['ir.cron'].sudo().search([('gsf_account_id', '=', self.id)])
        for record in self:
            record.gsf_account_cron_count = len(gsf_account_crons.ids)
    
    name = fields.Char(string='Name', required=True, help="Insert google shopping account name")
    gs_merchant_id = fields.Char("Merchant ID", help="Google merchant ID")
    gs_client_id = fields.Char("Client ID", help="Google client ID")
    gs_client_secret_key = fields.Char("Client Secret", help="Google client secret key")
    gs_client_auth_code = fields.Char("Auth Code", help="Client Auth Code")
    gs_client_auth_access_token = fields.Char("Auth Access Token", help="Auth Access Token")
    gs_client_auth_refresh_token = fields.Char("Auth Refresh Token", help="Refresh Token")
    gs_company_id = fields.Many2one("res.company", string="Company", help="Company")
    gs_instances_count = fields.Integer(string='Shopping Instances Count', compute='_compute_shopping_instances_ids')
    gs_instance_ids = fields.One2many("google.shopping.feed.instance", "gs_account_id",
                                      string="Google Shopping Instances", help="Google shopping instances")
    state = fields.Selection([
        ('new', 'New'),
        ('authorized', 'Authorized'),
        ('confirmed', 'Confirmed'),
    ], default='new', help="State")
    warehouse_ids = fields.Many2many('stock.warehouse', 'google_shopping_gcs_stock_warehouse_rel',
                                    domain="[('company_id', '=', gs_company_id)]",
                                    string="Warehouses", help="Select warehouses")
    stock_field = fields.Many2one('ir.model.fields', string='Stock Field')
    # google_shopping_account_claim_file = fields.Binary("Verification HTML File", filename="google_shopping_account_claim_filename", attachment=True, copy=False, help="You can upload HTML file which is downloaded from Google Merchant account and ")
    google_shopping_account_claim_filename = fields.Char(string='Verification HTML File Name', size=256)
    gs_website_id = fields.Many2one("website", string="Website", help="Select website")
    gs_website_domain = fields.Char("Website Domain", related="gs_website_id.domain", readonly=False)
    gs_authorized_redirect_uri = fields.Char("Authorized Redirect URI", compute="get_and_set_authorized_redirect_uri", store=True)
    gsf_account_cron_count = fields.Integer("Shopping Account Scheduler Count", compute="_compute_gsf_account_crons", help="This Field relocates Active Scheduler Count.")
    
    # Cron Fields
    # Auto Update Products in Google Shopping
    is_auto_update_products_in_gsf = fields.Boolean("Auto Update Products in Google Shopping?", copy=False, 
                                                    default=False)
    is_auto_update_products_inventory_info_in_gsf = fields.Boolean(
        "Auto Update Products Inventory Info. in Google Shopping?", copy=False, default=False)
    is_auto_get_products_status_from_gsf = fields.Boolean("Auto Get Products Status from Google Shopping?", 
                                                          copy=False, default=False)
    is_auto_import_products_info_from_gsf = fields.Boolean("Auto Import Product Info. from Google Shopping?", 
                                                           copy=False, default=False)
    
    # Odoo Logic Section
    # =====================
    def action_view_shopping_instances(self):
        """
            This function returns an action that display existing delivery orders
            of given sales order ids. It can either be a in a list or in a form
            view, if there is only one delivery order to show.
            :return: action or error
        """
        action = self.env["ir.actions.actions"]._for_xml_id("google_shopping_feed_gcs.google_shopping_feed_instance_action")
        gs_instances = self.mapped('gs_instance_ids')
        if len(gs_instances) > 1:
            action['domain'] = [('id', 'in', gs_instances.ids)]
        elif gs_instances:
            form_view = [(self.env.ref('google_shopping_feed_gcs.google_shopping_feed_instance_form_view').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state, view) for state, view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = gs_instances.id
        return action
    
    def action_view_shopping_account_crons(self):
        gsf_account_crons = self.env['ir.cron'].sudo().search([('gsf_account_id', '=', self.id)])
        action = {
            'domain': "[('id', 'in', " + str(gsf_account_crons.ids) + " )]",
            'name': "Shopping Account's Schedulers",
            'view_mode': 'tree,form',
            'res_model': 'ir.cron',
            'type': 'ir.actions.act_window',
        }
        return action
    
    def action_open_gsf_crons_setting_view(self):
        view_id = self.env.ref('google_shopping_feed_gcs.gsf_crons_setting_from_view', False)
        ctx = dict(self.env.context)
        ctx.update({'gsf_account_id': self.id})
        action = {
            'name': 'Google Shopping Account Crons Setting',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'gsf.crons.settings',
            'type': 'ir.actions.act_window',
            'view_id': view_id.id,
            'target': 'new',
            'context': ctx,
        }
        return action
    
    def unlink(self):
        for shopping_account in self:
            if shopping_account.gs_instance_ids:
                raise UserError(_('You can not delete Shopping Account. You must first delete Shopping Instances related to this Shopping Account.'))
            if shopping_account.state in ('confirmed', 'authorized'):
                raise UserError(_('You can not delete Confirmed or Authorized Shopping Account. You must first Reset to New Google Shopping Account.'))
        return super(GoogleShoppingFeedAccount, self).unlink()
    
    def reset_to_new(self):
        for shopping_account in self:
            shopping_account.write({'state': 'new'})
            shopping_account.gs_instance_ids and shopping_account.gs_instance_ids.write({'state': 'new'})
        return True
    
    def reset_to_authorized(self):
        for shopping_account in self:
            shopping_account.write({'state': 'authorized'})
            shopping_account.gs_instance_ids and shopping_account.gs_instance_ids.write({'state': 'new'})
        return True
    
    @api.constrains('gs_merchant_id')
    def _check_duplicate_google_shopping_account(self):
        gs_accounts = self.search([('gs_merchant_id', '=', self.gs_merchant_id)])
        if gs_accounts and len(gs_accounts) > 1:
            raise ValidationError(_('You can not create same duplicate Google Shopping Account with same Google Shopping Account Merchant ID.'))
        return True 
        
    def authorize_gsf_account(self):
        """
            This method call to,
            1. Redirect Google Auth Code website
            2. Get Authorization code
            3. Set Authorization Code in Google Shopping Account.
            4. Redirect to Odoo Home Screen in new tab.
            :return: Action
        """
        GoogleShoppingAPIObj = GoogleShoppingAPI()
        return GoogleShoppingAPIObj.authorize_gsf_account(self)
        
    @api.model
    def set_authorize_gs_code(self, gsf_account_id, authorization_code):
        """
            This method call to Set Authorization Code which are get from Google.
            :return: empty
        """
        gsf_account = self.browse(gsf_account_id)
        vals = {
            'gs_client_auth_code': authorization_code or '',
            'gs_client_auth_refresh_token': '',
            'gs_client_auth_access_token': '',
            'state': 'authorized'
        }
        gsf_account and authorization_code and gsf_account.sudo().write(vals)
        return True
    
    def get_gsf_tokens(self):
        """
            This method call to get Access and Refresh Token using Authorization Code.
            :return: True
        """
        GoogleShoppingAPIObj = GoogleShoppingAPI()
        response_obj = GoogleShoppingAPIObj._get_google_token_json(self)
        if response_obj.status_code == 200:
            response = response_obj.json()
            vals = {
                'gs_client_auth_refresh_token': response.get('refresh_token'),
                'gs_client_auth_access_token': response.get('access_token'),
                'state': 'confirmed'
            }
            self.write(vals)
        return True
    
    def get_gsf_refresh_tokens(self):
        """
            This method call to Re-Generate Access Token using Refresh Token. 
            :return: True
        """
        GoogleShoppingAPIObj = GoogleShoppingAPI()
        response_obj = GoogleShoppingAPIObj._refresh_google_token_json(self)
        if response_obj.status_code == 200:
            response = response_obj.json()
            vals = {
                'gs_client_auth_access_token': response.get('access_token'),
            }
            self.write(vals)
        return True
    
    def claim_your_website_with_google(self):
        if not self.google_shopping_account_claim_filename:
            raise UserError(_("Please first insert the Verification File Name after you can verify your website with google. "))
        return {
            'type': 'ir.actions.act_url',
            'url': "%s/%s" % (self.gs_website_domain, self.google_shopping_account_claim_filename),
            'nodestroy': True,
            'target': 'new'
        }
        
    def auto_update_products_in_gsf_cron(self, args=None):
        """
            This method call to update exported products of the selected instances.
            :return: True or Error
        """
        gsf_product_variants_obj = self.env['google.shopping.product.variants']
        gsf_account_id = self.browse(args.get("gsf_account_id", False))
        instances = gsf_account_id.gs_instance_ids.filtered(lambda x: x.state == "confirmed")
        shopping_products = gsf_product_variants_obj.search([
            ('exported_in_google_shopping', '=', True),
            ('gs_instance_id.state', '=', 'confirmed'),
            ('gs_instance_id', 'in', instances.ids),
            ('google_product_id', '!=', '')
        ])
        shopping_products and shopping_products.update_products_in_google_shopping()
        return True    
    
    def auto_update_products_inventory_info_in_gsf_cron(self, args=None):
        gsf_product_variants_obj = self.env['google.shopping.product.variants']
        gsf_account_id = self.browse(args.get("gsf_account_id", False))
        instances = gsf_account_id.gs_instance_ids.filtered(lambda x: x.state == "confirmed")
        
        shopping_products = gsf_product_variants_obj.search([
            ('exported_in_google_shopping', '=', True),
            ('gs_instance_id.state', '=', 'confirmed'),
            ('gs_instance_id', 'in', instances.ids),
            ('google_product_id', '!=', '')
        ])
        shopping_products and shopping_products.update_product_inventory_info()
        return True    
    
    def auto_get_products_status_from_gsf_cron(self, args=None):
        """
            This method call to import google shopping products of the selected instances and account.
            :return: True or Error
        """
        gsf_product_variants_obj = self.env['google.shopping.product.variants']
        gsf_account_id = self.browse(args.get("gsf_account_id", False))
        instances = gsf_account_id.gs_instance_ids.filtered(lambda x: x.state == "confirmed")
        shopping_products = gsf_product_variants_obj.search([
            ('exported_in_google_shopping', '=', True),
            ('gs_instance_id.state', '=', 'confirmed'),
            ('gs_instance_id', 'in', instances.ids),
            ('google_product_id', '!=', '')
        ])
        shopping_products and shopping_products.get_product_status_from_google_shopping()
        return True
    
    def auto_import_products_info_from_gsf_cron(self, args=None):
        """
            This method call to import google shopping products of the selected instances and account.
            :return: True or Error
        """
        gsf_product_variants_obj = self.env['google.shopping.product.variants']
        gsf_account_id = self.browse(args.get("gsf_account_id", False))
        instances = gsf_account_id.gs_instance_ids.filtered(lambda x: x.state == "confirmed")
        gsf_product_variants_obj.import_google_shopping_products(instances, gsf_account_id)
        return True
