from odoo import fields, models, api, _
import requests
import json


class FFNAuthorize(models.TransientModel):
    _name = 'ffn.authorize'
    _description = 'FFN Authorize'

    product_id = fields.Many2one('product.template', domain="[('jfsku', '!=', False)]")
    sku = fields.Char(related='product_id.jfsku', store=True, string='JFSKU')
    partner_id = fields.Many2one('res.partner', required=True, domain="[('ffn_id', '!=', False)]", store='Fulfiller')
    show_grant_all = fields.Boolean()
    grant_all = fields.Boolean()

    def get_headers(self):
        company = self.env.company
        return {
            "x-application-id": company.ffn_application_id,
            "x-application-version": company.ffn_application_version,
            "Authorization": company.ffn_token,
            "Accept": "application/json",
            "content-type": "application/json",
        }
    def button_grant_authorize(self):
        data = {
            "fulfillerId": self.partner_id.ffn_id
        }
        if self.grant_all:
            if self.env.company.ffn_env_type == 'production':
                url = f"https://ffn.api.jtl-software.com/api/v1/merchant/products/authorizations"
            else:
                url = f"https://ffn-sbx.api.jtl-software.com/api/v1/merchant/products/authorizations"
        else:
            if self.env.company.ffn_env_type == 'production':
                url = f"https://ffn.api.jtl-software.com/api/v1/merchant/products/{self.sku}/authorizations"
            else:
                url = f"https://ffn-sbx.api.jtl-software.com/api/v1/merchant/products/{self.sku}/authorizations"
        response = requests.post(url, data=json.dumps(data), headers=self.get_headers())
        if response.status_code == 201:
            if self.grant_all:
                products = self.env['product.template'].search([('jfsku', '!=', False)])
                for p in products:
                    p.authorized_partner_ids = [(4, self.partner_id.id)]
            else:
                self.product_id.authorized_partner_ids = [(4, self.partner_id.id)]
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

    def button_delete_authorize(self):
        if self.env.company.ffn_env_type == 'production':
            url = f"https://ffn.api.jtl-software.com/api/v1/merchant/products/{self.sku}/authorizations/{self.partner_id.ffn_id}"
        else:
            url = f"https://ffn-sbx.api.jtl-software.com/api/v1/merchant/products/{self.sku}/authorizations/{self.partner_id.ffn_id}"
        response = requests.delete(url, headers=self.get_headers())
        if response.status_code == 204:
            self.product_id.authorized_partner_ids = [(3, self.partner_id.id)]
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'target': 'new',
                'params': {
                    'title': 'Success',
                    'message': _("Product authorization removed Successfully!"),
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
                            'title': data['errorMessages'][0]['target'] if data['errorMessages'][0].get("target",
                                                                                                        False) else 'Error',
                            'message': data['errorMessages'][0]['message'],
                            'type': 'danger',
                            'sticky': False,
                            'next': {'type': 'ir.actions.act_window_close'},
                        }
                    }

