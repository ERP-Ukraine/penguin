# -*- coding: utf-8 -*-
# !/usr/bin/python3
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import json
import requests
import logging
from werkzeug import urls

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

GS_AUTH_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
GS_SCOP = "https://www.googleapis.com/auth/content"
GS_TOKEN_ENDPOINT = 'https://oauth2.googleapis.com/token'
GS_PRODUCT_API = "https://www.googleapis.com/content/v2.1/%s/products"
GS_GET_PRODUCT_BY_ID_API = "https://www.googleapis.com/content/v2.1/%s/products/%s"
GSF_DELETE_PRODUCT_BY_ID = "https://www.googleapis.com/content/v2.1/%s/products/%s"
GS_GET_PRODUCTS_API = "https://www.googleapis.com/content/v2.1/%s/products"
# GS_UPDATE_PRODUCT_INVENTORY_INFO_API = "https://www.googleapis.com/content/v2/%s/inventory/online/products/%s"
GS_UPDATE_PRODUCT_INVENTORY_INFO_API = "https://www.googleapis.com/content/v2.1/%s/products/%s"
GS_GET_PRODUCT_STATUS_API = "https://www.googleapis.com/content/v2.1/%s/productstatuses/%s"
ODOO_DEFAULT_URL = "http://www.odoo.com?NoBaseUrl"
ODOO_REDIRECT_ENDPOINT = "/google_account/authentication2"


class GoogleShoppingAPI:
    # Get Authorization Code Section
    def authorize_gsf_account(self, gs_account):
        """
            This method call to,
            1. Redirect Google Auth Code website
            2. Get Authorization code
            3. Set Authorization Code in Odoo Google Shopping Account.
            4. Redirect to Odoo Home Screen in new tab.
            :return: Action
        """
        url = self._get_authorize_uri(gs_account)
        return {
            'type': 'ir.actions.act_url',
            'name': "Authorize Account",
            'target': 'new',
            'url': url
        }

    def _get_authorize_uri(self, gs_account):
        """
            This method call to get authorize URL and return it.
            @return: url
        """
        get_param = gs_account.env['ir.config_parameter'].sudo().get_param
        base_url = get_param('web.base.url', default=ODOO_DEFAULT_URL)
        gs_client_id = gs_account.gs_client_id

        state = json.dumps({
            'database': gs_account.env.cr.dbname,
            'base_url': gs_account.gs_website_domain,  # base_url,
            'gs_account': gs_account.id
        })
        encoded_params = urls.url_encode({
            'response_type': 'code',
            'client_id': gs_client_id,
            'state': state,
            'scope': GS_SCOP,
            'redirect_uri': gs_account.gs_authorized_redirect_uri or ODOO_DEFAULT_URL,
            # base_url + ODOO_REDIRECT_ENDPOINT,
            # 'approval_prompt': 'force',
            'prompt': 'consent',
            'access_type': 'offline'
        })
        return "%s?%s" % (GS_AUTH_ENDPOINT, encoded_params)

    # Get Authorization Token Section
    def _get_google_token_json(self, gs_account):
        """ Call Google API to exchange authorization code against token, with POST request, to
            not be redirected.
        """
        get_param = gs_account.env['ir.config_parameter'].sudo().get_param
        base_url = get_param('web.base.url', default=ODOO_DEFAULT_URL)
        client_id = gs_account.gs_client_id
        client_secret = gs_account.gs_client_secret_key
        authorize_code = gs_account.gs_client_auth_code

        headers = {"content-type": "application/x-www-form-urlencoded"}
        data = {
            'code': authorize_code,
            'client_id': client_id,
            'client_secret': client_secret,
            'grant_type': 'authorization_code',
            'redirect_uri': gs_account.gs_authorized_redirect_uri or ODOO_DEFAULT_URL
            # base_url + ODOO_REDIRECT_ENDPOINT
        }
        try:
            response = requests.post(GS_TOKEN_ENDPOINT, data=data, headers=headers, timeout=20)
            response.raise_for_status()
            return response
        except requests.HTTPError:
            error_msg = _("Something went wrong during your token generation. Maybe your Authorization Code is invalid")
            raise UserError(error_msg)

    # Get Authorization Refresh Token Section
    def _refresh_google_token_json(self, gs_account):
        client_id = gs_account.gs_client_id
        client_secret = gs_account.gs_client_secret_key
        client_auth_refresh_token = gs_account.gs_client_auth_refresh_token

        if not client_id or not client_secret:
            raise UserError(_("Client ID and/or Client Secret Key is missing so please first configure it."))
        if not client_auth_refresh_token:
            raise UserError(_("Missing Auth Tokens so, First generate Auth Tokens after try to get New Access Token."))

        headers = {"content-type": "application/x-www-form-urlencoded"}
        data = {
            'refresh_token': client_auth_refresh_token,
            'client_id': client_id,
            'client_secret': client_secret,
            'grant_type': 'refresh_token',
        }

        try:
            response = requests.post(GS_TOKEN_ENDPOINT, data=data, headers=headers, timeout=20)
            response.raise_for_status()
            return response
        except requests.HTTPError as error:
            if error.response.status_code == 400:
                gs_account.write({
                    'gs_client_auth_refresh_token': '',
                    'gs_client_auth_access_token': '',
                })
            error_key = error.response.json().get("error", "nc")
            error_msg = _(
                "Something went wrong during your token generation. "
                "Maybe your Authorization Code is invalid or already expired [%s]") % error_key
            raise UserError(error_msg)

    # Post product into Google Shopping Center Part
    def export_product_in_gsf_api(self, gs_account, product_dict):
        export_product_in_gsf_api_url = GS_PRODUCT_API % gs_account.gs_merchant_id
        headers = {
            "Content-type": "application/json",
            'Authorization': "Bearer %s" % gs_account.gs_client_auth_access_token,
        }
        try:
            req_obj = requests.post(export_product_in_gsf_api_url, data=json.dumps(product_dict), headers=headers,
                                    timeout=20)
        except Exception as e:
            error_msg = _("Something went wrong during call Export Product API. \nError: %s" % e)
            raise UserError(error_msg)
        return req_obj

    # Update product metadata into Google Shipping Center Part
    def update_product_in_google_shopping_api(self, gs_account_id, product_dict):
        gsf_product_api_url = GS_PRODUCT_API % gs_account_id.gs_merchant_id
        headers = {
            "Content-type": "application/json",
            'Authorization': "Bearer %s" % gs_account_id.gs_client_auth_access_token,
        }
        try:
            req_obj = requests.post(gsf_product_api_url, data=json.dumps(product_dict), headers=headers, timeout=20)
        except Exception as e:
            error_msg = _("Something went wrong during call Update Product API. \nError: %s" % e)
            raise UserError(error_msg)
        return req_obj

    # Get product metadata by product id into Odoo Google Shopping Center Part
    def import_product_info_from_gsf_by_id_api(self, gs_account_id, google_product_id):
        import_product_info_api_url = GS_GET_PRODUCT_BY_ID_API % (gs_account_id.gs_merchant_id, google_product_id)
        headers = {
            "Content-type": "application/json",
            'Authorization': "Bearer %s" % gs_account_id.gs_client_auth_access_token,
        }
        try:
            req_obj = requests.get(import_product_info_api_url, headers=headers, timeout=20)
        except Exception as e:
            error_msg = _("Something went wrong during call Import Product API. \nError: %s" % e)
            raise UserError(error_msg)
        return req_obj

    def delete_products_in_google_shopping_by_id_api(self, gs_account_id, google_product_id):
        gsf_delete_product_api_url = GSF_DELETE_PRODUCT_BY_ID % (gs_account_id.gs_merchant_id, google_product_id)
        headers = {
            "Content-type": "application/json",
            'Authorization': "Bearer %s" % gs_account_id.gs_client_auth_access_token,
        }
        try:
            req_obj = requests.delete(gsf_delete_product_api_url, headers=headers, timeout=20)
        except Exception as e:
            error_msg = _("Something went wrong during call Delete Product API. \nError: %s" % e)
            raise UserError(error_msg)
        return req_obj

    def import_google_shopping_products_api(self, gs_account_id):
        gsf_import_products_api_url = GS_GET_PRODUCTS_API % gs_account_id.gs_merchant_id
        headers = {
            "Content-type": "application/json",
            'Authorization': "Bearer %s" % gs_account_id.gs_client_auth_access_token,
        }
        try:
            req_obj = requests.get(gsf_import_products_api_url, headers=headers, timeout=20)
        except Exception as e:
            error_msg = _("Something went wrong during call Get All Products via Operations API. \nError: %s" % e)
            raise UserError(error_msg)
        return req_obj

    def update_product_inventory_info_api(self, gs_account_id, product_dict, google_product_id):
        gsf_update_inventory_info_api_url = GS_UPDATE_PRODUCT_INVENTORY_INFO_API % (
            gs_account_id.gs_merchant_id, google_product_id)
        headers = {
            "Content-type": "application/json",
            'Authorization': "Bearer %s" % gs_account_id.gs_client_auth_access_token,
        }
        try:
            req_obj = requests.patch(gsf_update_inventory_info_api_url, data=json.dumps(product_dict), headers=headers,
                                     timeout=20)
        except Exception as e:
            error_msg = _("Something went wrong during call Update Product Inventory Info API. \nError: %s" % e)
            raise UserError(error_msg)
        return req_obj

    def get_product_status_from_google_shopping_api(self, gs_account_id, google_product_id):
        gsf_get_product_status_api_url = GS_GET_PRODUCT_STATUS_API % (gs_account_id.gs_merchant_id, google_product_id)
        headers = {
            "Content-type": "application/json",
            'Authorization': "Bearer %s" % gs_account_id.gs_client_auth_access_token,
        }
        try:
            req_obj = requests.get(gsf_get_product_status_api_url, headers=headers, timeout=20)
        except Exception as e:
            error_msg = _("Something went wrong during call Get Product Status via Operations API. \nError: %s" % e)
            raise UserError(error_msg)
        return req_obj
