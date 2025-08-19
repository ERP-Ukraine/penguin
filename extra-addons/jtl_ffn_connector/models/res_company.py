from odoo import fields, models
import requests
import json
from requests.auth import HTTPBasicAuth


class Company(models.Model):
    _inherit = 'res.company'

    enable_ffn = fields.Boolean(string='Enable FFN')
    ffn_application_id = fields.Char(string='FFN Application ID')
    ffn_application_version = fields.Char(string='FFN Application Version')
    ffn_token = fields.Char(string='FFN Token')
    ffn_refresh_token = fields.Char(string='FFN Refresh Token')
    ffn_env_type = fields.Selection(selection=[
        ('sandbox', 'Sandbox'),
        ('production', 'Production'),
    ])
    ffn_client_id = fields.Char(string='FFN Client ID')
    ffn_client_secret = fields.Char(string='FFN Client Secret')

    def get_all_ffn_refresh_token(self):
        companies = self.env['res.company'].sudo().search([('enable_ffn', '=', True)])
        for company in companies:
            company.get_ffn_refresh_token()

    def get_ffn_refresh_token(self):
        url = "https://oauth2.api.jtl-software.com/token"
        client_id = self.ffn_client_id
        client_secret = self.ffn_client_secret
        data = {
            "grant_type": "refresh_token",
            "refresh_token": self.ffn_refresh_token,
        }
        response = requests.post(url, data=data, auth=HTTPBasicAuth(client_id, client_secret))
        if response.content:
            data = json.loads(response.content.decode())
            if response.status_code == 200:
                self.ffn_token = f"Bearer {data['access_token']}"
                self.ffn_refresh_token = data['refresh_token']
