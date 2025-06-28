# coding: utf-8
# Part of PIT Solutions AG. See LICENSE file for full copyright and licensing details.

import logging
import requests
from pprint import pformat
from time import time
from datetime import datetime
import hashlib
import hmac
import base64
import json
from werkzeug import urls
from psycopg2 import OperationalError, Error

from odoo import api, models, fields, tools, _
from odoo.http import request
from odoo.addons.payment.models.payment_acquirer import ValidationError
from odoo.addons.payment_wallee.controllers.main import WalleeController
from odoo.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.addons.payment import utils as payment_utils

_logger = logging.getLogger(__name__)

TIMEOUT = 20


class PaymentAcquirerWallee(models.Model):
    _inherit = 'payment.acquirer'

    WALLEE_API_PROD_BASE_URL = "app-wallee.com"
    WALLEE_API_TEST_BASE_URL = "app-wallee.com"

    def _get_wallee_urls(self, environment):
        if environment == 'prod':
            return {'wallee_form_url': 'https://app-wallee.com'}
        else:
            return {'wallee_form_url': 'https://app-wallee.com'}

    # calculatiing key
    @api.model
    def wallee_sign(self, wallee_acquirer, method, path, timestamp):
        userId = wallee_acquirer.sudo().wallee_api_userid
        secret = wallee_acquirer.sudo().wallee_api_application_key
        data = "1|" + str(userId) + "|" + str(timestamp) + "|" + method + "|" + path
        signature = ((base64.b64encode(hmac.new(base64.b64decode(bytearray(secret, "ASCII")), bytearray(data, "ASCII"),
                                                hashlib.sha512).digest())).decode("ASCII")).replace("\n", "")
        return signature

    # send request with key
    @api.model
    def wallee_send_request(self, wallee_acquirer_id, type, uri, params={}, json_data={}, data={}, headers={}):
        _logger.info("Requesting Wallee Services \nAcquirer Id:\n%s\nType:\n%s\nURL:\n%s", \
                     pformat(wallee_acquirer_id), \
                     pformat(type), \
                     pformat(uri))
        wallee_acquirer_id = int(wallee_acquirer_id)
        wallee_acquirer = self.browse(wallee_acquirer_id)
        ask_time = fields.Datetime.now()
        result = {'ask_time': ask_time}
        response = {}
        try:
            timestamp = str(int(time()))
            userId = str(wallee_acquirer.sudo().wallee_api_userid)
            secret = str(wallee_acquirer.sudo().wallee_api_application_key)
            signature = str(wallee_acquirer.wallee_sign(wallee_acquirer, type, uri, timestamp))
            headers.update({"Content-type": "application/json", \
                            "x-mac-version": "1", \
                            "x-mac-userid": userId, \
                            "x-mac-timestamp": timestamp, \
                            "x-mac-value": signature})
            acquirer_env = wallee_acquirer.state
            acquirer_base_url = wallee_acquirer.WALLEE_API_PROD_BASE_URL if acquirer_env == 'enabled' else wallee_acquirer.WALLEE_API_TEST_BASE_URL
            request_uri = "".join(['https://', acquirer_base_url, uri])
            if type.upper() in ('GET', 'DELETE'):
                res = requests.request(type.lower(), request_uri, params=params, headers=headers, timeout=TIMEOUT)
            elif type.upper() in ('POST', 'PATCH', 'PUT'):
                res = requests.request(type.lower(), request_uri, params=params, data=data, json=json_data,
                                       headers=headers, timeout=TIMEOUT)
            else:
                raise Exception(_('Method not supported [%s] not in [GET, POST, PUT, PATCH or DELETE]!') % (type))
            res.raise_for_status()
            status = res.status_code
            try:
                response = res.json()
            except Exception as e:
                _logger.info("Error! wallee_send_request json reterival %s" % (e,))
                res_data = res.request.body
                res_data = res.content
                res_data = res.text
                response = res_data
            try:
                ask_time = datetime.strptime(res.headers.get('date'), "%a, %d %b %Y %H:%M:%S %Z")
                result.update({'ask_time': ask_time})
            except:
                pass
            if status in [200]:
                _logger.info("Successfully executed Wallee Services \nAcquirer Id:\n%s\nType:\n%s\nURL:\n%s", \
                             pformat(wallee_acquirer_id), \
                             pformat(type), \
                             pformat(uri))
                # _logger.info("Successfully executed Wallee Services \nURL:\n%s\nRequest:\n%s", \
                #             pformat(uri), \
                #             pformat(json_data))
                # _logger.info("Successfully executed Wallee Services \nURL:\n%s\nResponse:\n%s", \
                #                pformat(uri), \
                #                pformat(response))

        except requests.HTTPError as error:
            status = error.response.status_code
            try:
                req = json.loads(error.request.body)
            except Exception as e:
                _logger.info("HTTPError! wallee_send_request json reterival :: req %s" % (e,))
                req = error.request.body
            try:
                res = error.response.json()
                message = res.get('defaultMessage', False)
                if not message:
                    message = res.get('message', '')
                result.update({'error': message})
            except Exception as e:
                _logger.info("HTTPError! wallee_send_request :: res %s" % (e,))
                result.update({'error': _('Unknown Wallee Error %s' % (e,))})
                res = {}
            response = res
            if status in [442]:
                _logger.info("Client Error while requesting Wallee Services\nRequest:\n%s\nResponse:\n%s", \
                             pformat(req), pformat(res))
            elif status in [409]:
                _logger.info("Client Error (Conflict) while requesting Wallee Services\nRequest:\n%s\nResponse:\n%s", \
                             pformat(req), pformat(res))
            elif status in [542]:
                _logger.info("Server Error while requesting Wallee Services\nRequest:\n%s\nResponse:\n%s", \
                             pformat(req), pformat(res))
            elif status in [401]:
                _logger.info("Unauthorized Error while requesting Wallee Services\nRequest:\n%s\nResponse:\n%s", \
                             pformat(req), pformat(res))
        except Exception as e:
            _logger.info("Error! Unknown Error while requesting Wallee Services")
            status = 500
            result.update({'error': _('Unknown Error %s' % (e,))})
        result.update({'status': status, 'data': response})
        self.env['payment.acquirer.log']._post_log({
            'name': result['status'],
            'detail': "%s" % (result['data'],),
            'type': 'green',
        })
        return result

    def _compute_wallee_feature_support(self):
        feature_support = self._get_feature_support()
        for acquirer in self:
            hide_registration_templ = feature_support.get('hide_registration_templ', [])
            hide_specific_countries = feature_support.get('hide_specific_countries', [])
            hide_payment_icon_ids = feature_support.get('hide_payment_icon_ids', [])
            hide_env_button = feature_support.get('hide_env_button', [])
            acquirer.hide_registration_templ = acquirer.provider in hide_registration_templ
            acquirer.hide_specific_countries = acquirer.provider in hide_specific_countries
            acquirer.hide_payment_icon_ids = acquirer.provider in hide_payment_icon_ids
            acquirer.hide_env_button = acquirer.provider in hide_env_button

    provider = fields.Selection(selection_add=[('wallee', 'Wallee')], ondelete={'wallee': 'set default'})
    wallee_api_userid = fields.Integer(required_if_provider='wallee', string='Rest API UserID',
                                       groups='base.group_user')
    wallee_api_spaceid = fields.Integer(required_if_provider='wallee', string='Rest API SpaceId',
                                        groups='base.group_user')
    wallee_api_application_key = fields.Char(required_if_provider='wallee', string='Application Key',
                                             groups='base.group_user')
    wallee_method_ids = fields.One2many('wallee.payment.method', 'acquirer_id', 'Supported Wallee Payment Methods')
    hide_registration_templ = fields.Boolean('Hide S2S Form Template', compute='_compute_wallee_feature_support')
    hide_specific_countries = fields.Boolean('Hide Specific Countries', compute='_compute_wallee_feature_support')
    hide_payment_icon_ids = fields.Boolean('Hide Payment Icons', compute='_compute_wallee_feature_support')
    hide_env_button = fields.Boolean('Hide Env Button', compute='_compute_wallee_feature_support')
    send_status_email = fields.Boolean('Send Status Email', default=True)

    def _get_default_payment_method_id(self):
        self.ensure_one()
        if self.provider != 'wallee':
            return super(PaymentAcquirerWallee, self)._get_default_payment_method_id()
        return self.env.ref('payment_wallee.payment_method_wallee').id

    @api.model
    def create(self, vals):
        res = super(PaymentAcquirerWallee, self).create(vals)
        if 'wallee_api_userid' in vals \
                or 'wallee_api_spaceid' in vals \
                or 'wallee_api_application_key' in vals:
            res.update_wallee_payment_methods()
        return res

    def write(self, values):
        res = super(PaymentAcquirerWallee, self).write(values)
        if 'wallee_api_userid' in values \
                or 'wallee_api_spaceid' in values \
                or 'wallee_api_application_key' in values:
            self.update_wallee_payment_methods()
        return res

    def _get_feature_support(self):
        res = {}
        res.update({
            'hide_registration_templ': ['wallee'],
            'hide_specific_countries': ['wallee'],
            'hide_payment_icon_ids': ['wallee'],
            'hide_env_button': ['wallee'],
        })
        return res

    def action_view_wallee_payment_methods(self):
        self.ensure_one()
        self.get_available_wallee_payment_methods(self.id)
        action = self.env.ref('payment_wallee.action_wallee_payment_method').read()[0]
        return action

    @api.model
    def get_available_wallee_payment_methods(self, wallee_acquirer_id):
        wallee_acquirer_id = int(wallee_acquirer_id)
        wallee_acquirer = self.browse(wallee_acquirer_id)
        spaceId = wallee_acquirer.sudo().wallee_api_spaceid
        lang = 'en'
        if request:
            try:
                lang = request.lang and request.lang.split('_')[0] or 'en'
            except Exception:
                lang = self.env.user.lang and self.env.user.lang.split('_')[0] or 'en'

        json_data = {"language": lang}
        uri = "/api/payment-method-configuration/search?spaceId=%s" % spaceId
        type = "POST"
        response = wallee_acquirer.wallee_send_request(wallee_acquirer_id, \
                                                       type=type, uri=uri, \
                                                       json_data=json_data)

        status = response.get('status', 0)
        data = response.get('data', [])
        wallee_payment_methods = []
        if status == 200 and data:
            for pay_method in data:
                name = pay_method.get('name', False)
                sequence = pay_method.get('sortOrder', 10)
                acquirer_id = wallee_acquirer.id
                space_id = pay_method.get('spaceId', False)
                method_id = pay_method.get('id', False)
                image_url = pay_method.get('resolvedImageUrl', False)
                oneClickPaymentMode = pay_method.get('oneClickPaymentMode', False)
                one_click = 1 if oneClickPaymentMode == 'ALLOW' else 0
                payment_method_ref = pay_method.get('paymentMethod', False)
                transaction_interface = pay_method.get('dataCollectionType', False)
                state = pay_method.get('state', False)
                active = True if state == 'ACTIVE' else False
                version = pay_method.get('version', False)
                values = {
                    'name': name,
                    'sequence': sequence,
                    'acquirer_id': acquirer_id,
                    'space_id': space_id,
                    'method_id': method_id,
                    'image_url': image_url,
                    'one_click': one_click,
                    'one_click_mode': oneClickPaymentMode,
                    'payment_method_ref': payment_method_ref,
                    'transaction_interface': transaction_interface,
                    'active': active,
                    'version': version,
                }
                wallee_payment_methods.append(values)
        return wallee_payment_methods

    @api.model
    def get_available_wallee_trans_payment_methods(self, wallee_acquirer_id, currency_name, amount, origin,
                                                   billing_partner_id):
        wallee_acquirer_id = int(wallee_acquirer_id)
        if currency_name == '' or amount == 0.0 or origin == '':
            return self.get_available_wallee_payment_methods(wallee_acquirer_id)
        wallee_acquirer = self.browse(wallee_acquirer_id)
        spaceId = wallee_acquirer.sudo().wallee_api_spaceid
        wallee_payment_method = request.session.get('wallee_payment_method', {})
        trans_id = wallee_payment_method.get('trans_id', 0)
        tx_details = {
            'currency_name': currency_name,
            'name': '-'.join(['TEMPTR', origin])
        }
        txline_details = [{
            'name': _("Total"),
            'quantity': 1,
            "type": "PRODUCT",
            "uniqueId": _("total"),
            "amountIncludingTax": amount,
        }]
        billing_address = {}
        if billing_partner_id:
            billing_partner = self.env['res.partner'].search([('id', '=', billing_partner_id)], limit=1)
            partner_first_name, partner_last_name = payment_utils.split_partner_name(billing_partner.name)
            partner_street = payment_utils.format_partner_address(billing_partner.street, billing_partner.street2)
            billing_address = {
                "city": billing_partner.city if billing_partner.city else "",
                "emailAddress": billing_partner.email if billing_partner.email else "",
                "givenName": partner_last_name if billing_partner else "",
                "familyName": partner_first_name if billing_partner else "",
                "phoneNumber": billing_partner.phone if billing_partner.phone else "",
                "organizationName": billing_partner.company_id.name if billing_partner.company_id else "",
                "postcode": billing_partner.zip if billing_partner.zip else "",
                "street": partner_street if partner_street else billing_partner.street,
                "state": billing_partner.state_id.name if billing_partner.state_id else "",
                "country": billing_partner.country_id.code if billing_partner.country_id else "",
                "postalState": billing_partner.state_id.code if billing_partner.state_id else "",
            }

        wallee_tx_values = {'tx_details': tx_details, 'txline_details': txline_details,
                            'billing_address': billing_address}
        wallee_create = True
        if trans_id:
            search_params = {'acquirer_reference': trans_id}
            response = self.wallee_search_transation_id(self.id, search_params)
            status = response.get('status', 0)
            data = response.get('data', [])
            wallee_version = ''
            wallee_state = False
            if status == 200 and data:
                wallee_trans = data[0]
                wallee_version = wallee_trans.get('version', '')
                wallee_state = wallee_trans.get('state', False)
            if wallee_version and wallee_state and wallee_state in ['CREATE', 'PENDING']:
                search_params = {'acquirer_reference': trans_id, 'version': wallee_version}
                response = self.wallee_update_transation_id(self.id, search_params, wallee_tx_values)
                wallee_create = False
        if wallee_create:
            response = self.wallee_create_transation(wallee_acquirer_id, wallee_tx_values)
            trans_id = response.get('trans_id', False)
        uri = "/api/transaction/fetchPossiblePaymentMethods?spaceId=%s&id=%s" % (spaceId, trans_id)
        type = "GET"
        response = wallee_acquirer.wallee_send_request(wallee_acquirer_id, \
                                                       type=type, uri=uri)
        status = response.get('status', 0)
        data = response.get('data', [])
        wallee_payment_methods = []
        lang = 'en_US'
        if request:
            try:
                lang = request.lang.code or 'en_US'
            except Exception:
                lang = self.env.user.lang.code or 'en_US'
            lang = lang.replace('_', '-')
        if status == 200 and data:
            for pay_method in data:
                name = pay_method.get('name', False)
                resolved_title = pay_method.get('resolvedTitle', {})
                name = resolved_title.get(lang, name)
                sequence = pay_method.get('sortOrder', 10)
                acquirer_id = wallee_acquirer.id
                space_id = pay_method.get('spaceId', False)
                method_id = pay_method.get('id', False)
                image_url = pay_method.get('resolvedImageUrl', False)
                oneClickPaymentMode = pay_method.get('oneClickPaymentMode', False)
                one_click = 1 if oneClickPaymentMode == 'ALLOW' else 0
                payment_method_ref = pay_method.get('paymentMethod', False)
                transaction_interface = pay_method.get('dataCollectionType', False)
                state = pay_method.get('state', False)
                active = True if state == 'ACTIVE' else False
                version = pay_method.get('version', False)
                values = {
                    'name': name,
                    'sequence': sequence,
                    'acquirer_id': acquirer_id,
                    'space_id': space_id,
                    'method_id': method_id,
                    'image_url': image_url,
                    'one_click': one_click,
                    'one_click_mode': oneClickPaymentMode,
                    'payment_method_ref': payment_method_ref,
                    'transaction_interface': transaction_interface,
                    'trans_id': trans_id,
                    'active': active,
                    'version': version,
                }
                wallee_payment_methods.append(values)
        return wallee_payment_methods

    def update_wallee_payment_methods(self):
        for acquirer in self:
            if acquirer.provider != 'wallee':
                continue
            acquirer.wallee_method_ids.unlink()
            try:
                PaymentIcon = self.env['payment.icon']
                WalleeMethod = self.env['wallee.payment.method']
                wallee_payment_methods = acquirer.get_available_wallee_payment_methods(acquirer.id)
                for pay_method in wallee_payment_methods:
                    payment_icon_name = pay_method.get('name', False)
                    payment_icon = PaymentIcon.search([('name', '=', payment_icon_name)], limit=1, order='id desc')
                    if not payment_icon:
                        payment_icon = PaymentIcon.create({'name': payment_icon_name})
                    name = payment_icon and payment_icon.id or False
                    pay_method.update({'name': name})
                    WalleeMethod.create(pay_method)
            except Exception as e:
                _logger.info("Error! update_available_payment_methods %s" % (e,))
        return

    @api.model
    def get_non_wallee_acquirers(self, acquirers):
        non_wallee_acquirers = [acq for acq in acquirers if acq.provider != 'wallee']
        return non_wallee_acquirers

    @api.model
    def get_wallee_acquirers(self, acquirers):
        wallee_acquirers = [acq for acq in acquirers if acq.provider == 'wallee']
        return wallee_acquirers

    @api.model
    def wallee_build_payment_page_url(self, wallee_acquirer_id, trans_id):
        wallee_acquirer_id = int(wallee_acquirer_id)
        wallee_acquirer = self.browse(wallee_acquirer_id)
        spaceId = wallee_acquirer.sudo().wallee_api_spaceid
        uri = "/api/transaction/buildPaymentPageUrl?spaceId=%s&id=%s" % (spaceId, trans_id)
        type = "GET"
        response = wallee_acquirer.wallee_send_request(wallee_acquirer_id, type=type, uri=uri)
        status = response.get('status', 0)
        data = response.get('data', [])
        error = response.get('error', _('Error cant be retrived'))
        res = {}
        if status == 200 and data:
            res = {'wallee_redirect_url': data}
        else:
            res = {'wallee_redirect_url': False, 'error': error}
        return res

    @api.model
    def wallee_build_javascript_url(self, wallee_acquirer_id, trans_id):
        wallee_acquirer_id = int(wallee_acquirer_id)
        wallee_acquirer = self.browse(wallee_acquirer_id)
        spaceId = wallee_acquirer.sudo().wallee_api_spaceid
        uri = "/api/transaction/buildJavaScriptUrl?spaceId=%s&id=%s" % (spaceId, trans_id)
        type = "GET"
        response = wallee_acquirer.wallee_send_request(wallee_acquirer_id, type=type, uri=uri)
        status = response.get('status', 0)
        data = response.get('data', [])
        error = response.get('error', _('Error cant be retrived'))
        res = {}
        if status == 200 and data:
            res = {'wallee_javascript_url': data}
        else:
            res = {'wallee_javascript_url': False, 'error': error}
        return res

    @api.model
    def wallee_search_payment_method_id(self, wallee_acquirer_id, payment_method_id):
        wallee_acquirer_id = int(wallee_acquirer_id)
        wallee_acquirer = self.browse(wallee_acquirer_id)
        spaceId = wallee_acquirer.sudo().wallee_api_spaceid
        uri = "/api/payment-method-configuration/read?spaceId=%s&id=%s" % (spaceId, payment_method_id)
        type = "GET"
        response = wallee_acquirer.wallee_send_request(wallee_acquirer_id, type=type, uri=uri)
        status = response.get('status', 0)
        data = response.get('data', [])
        error = response.get('error', _('Error cant be retrived'))
        res = {}
        if status == 200 and data:
            res = {'payment_method': data}
        else:
            res = {'payment_method': False, 'error': error}
        return res

    @api.model
    def wallee_search_transation_ref(self, wallee_acquirer_id, search_params):
        wallee_acquirer_id = int(wallee_acquirer_id)
        wallee_acquirer = self.browse(wallee_acquirer_id)
        spaceId = wallee_acquirer.sudo().wallee_api_spaceid
        uri = "/api/transaction/search?spaceId=%s" % spaceId
        type = "POST"
        reference = search_params.get('reference', '')
        json_data = {
            "filter": {
                "fieldName": "merchantReference",
                "operator": "EQUALS",
                "type": "LEAF",
                "value": reference
            }
        }
        response = wallee_acquirer.wallee_send_request(wallee_acquirer_id, \
                                                       type=type, uri=uri, \
                                                       json_data=json_data)
        status = response.get('status', 0)
        data = response.get('data', [])
        error = response.get('error', _('Error cant be retrived'))
        return response

    @api.model
    def wallee_search_transation_id(self, wallee_acquirer_id, search_params):
        wallee_acquirer_id = int(wallee_acquirer_id)
        wallee_acquirer = self.browse(wallee_acquirer_id)
        spaceId = wallee_acquirer.sudo().wallee_api_spaceid
        uri = "/api/transaction/search?spaceId=%s" % spaceId
        type = "POST"
        acquirer_reference = search_params.get('acquirer_reference', '')
        json_data = {
            "filter": {
                "fieldName": "id",
                "operator": "EQUALS",
                "type": "LEAF",
                "value": acquirer_reference
            }
        }
        response = wallee_acquirer.wallee_send_request(wallee_acquirer_id, \
                                                       type=type, uri=uri, \
                                                       json_data=json_data)
        status = response.get('status', 0)
        data = response.get('data', [])
        error = response.get('error', _('Error cant be retrived'))
        return response

    @api.model
    def wallee_search_transation_id_ref(self, wallee_acquirer_id, search_params):
        wallee_acquirer_id = int(wallee_acquirer_id)
        wallee_acquirer = self.browse(wallee_acquirer_id)
        spaceId = wallee_acquirer.sudo().wallee_api_spaceid
        uri = "/api/transaction/search?spaceId=%s" % spaceId
        type = "POST"
        reference = search_params.get('reference', '')
        acquirer_reference = search_params.get('acquirer_reference', '')
        json_data = {
            "filter": {
                "children": [
                    {
                        "fieldName": "id",
                        "operator": "EQUALS",
                        "type": "LEAF",
                        "value": acquirer_reference
                    },
                    {
                        "type": "AND"
                    },
                    {
                        "fieldName": "merchantReference",
                        "operator": "EQUALS",
                        "type": "LEAF",
                        "value": reference
                    }
                ]
            }
        }
        response = wallee_acquirer.wallee_send_request(wallee_acquirer_id, \
                                                       type=type, uri=uri, \
                                                       json_data=json_data)
        status = response.get('status', 0)
        data = response.get('data', [])
        error = response.get('error', _('Error cant be retrived'))
        return response

    @api.model
    def wallee_update_transation_id(self, wallee_acquirer_id, search_params, values):
        lang = 'en'
        if request:
            try:
                lang = request.lang and request.lang.split('_')[0] or 'en'
            except Exception:
                lang = self.env.user.lang and self.env.user.lang.split('_')[0] or 'en'
        wallee_acquirer_id = int(wallee_acquirer_id)
        wallee_acquirer = self.browse(wallee_acquirer_id)
        spaceId = wallee_acquirer.sudo().wallee_api_spaceid
        uri = "/api/transaction/update?spaceId=%s" % spaceId
        type = "POST"

        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        success_url = urls.url_join(base_url, WalleeController._success_url)
        failed_url = urls.url_join(base_url, WalleeController._failed_url)
        acquirer_reference = search_params.get('acquirer_reference', '')
        version = search_params.get('version')

        lineItems = values.get('txline_details')
        tx_details = values.get('tx_details')
        currency_name = tx_details.get('currency_name')
        merchantReference = tx_details.get('name')

        Transaction = self.env['payment.transaction']
        transaction = Transaction.search([('reference', '=', merchantReference)])
        success_url = transaction and "".join([success_url, '?txnId=', str(transaction.id)]) or success_url
        failed_url = transaction and "".join([failed_url, '?txnId=', str(transaction.id)]) or failed_url

        json_data = {
            'id': acquirer_reference,
            "language": lang,
            'lineItems': lineItems,
            'currency': currency_name,
            'merchantReference': merchantReference,
            "successUrl": success_url,
            "failedUrl": failed_url,
            "version": version,
        }

        billingAddress = values.get('billing_address', False)
        if billingAddress:
            json_data.update({'billingAddress': billingAddress})
        shippingAddress = values.get('shipping_address', False)
        if shippingAddress:
            json_data.update({'shippingAddress': shippingAddress})
        customerId = tx_details.get('partner_id', False)
        if customerId:
            json_data.update({'customerId': customerId})
        wallee_payment_method = values.get('wallee_payment_method', False)
        if wallee_payment_method:
            json_data.update({'allowedPaymentMethodConfigurations': [{'id': wallee_payment_method}]})
        else:
            json_data.update({'allowedPaymentMethodConfigurations': []})
        response = wallee_acquirer.wallee_send_request(wallee_acquirer_id, \
                                                       type=type, uri=uri, \
                                                       json_data=json_data)
        status = response.get('status', 0)
        data = response.get('data', [])
        error = response.get('error', _('Error cant be retrived'))
        return response

    @api.model
    def wallee_create_transation(self, wallee_acquirer_id, values):
        lang = 'en'
        if request:
            try:
                lang = request.lang and request.lang.split('_')[0] or 'en'
            except Exception:
                lang = self.env.user.lang and self.env.user.lang.split('_')[0] or 'en'
        wallee_acquirer_id = int(wallee_acquirer_id)
        wallee_acquirer = self.browse(wallee_acquirer_id)
        spaceId = wallee_acquirer.sudo().wallee_api_spaceid
        uri = "/api/transaction/create?spaceId=%s" % spaceId
        type = "POST"

        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        success_url = urls.url_join(base_url, WalleeController._success_url)
        failed_url = urls.url_join(base_url, WalleeController._failed_url)

        tx_details = values.get('tx_details')
        lineItems = values.get('txline_details')
        currency_name = tx_details.get('currency_name')
        merchantReference = tx_details.get('name')

        Transaction = self.env['payment.transaction']
        transaction = Transaction.search([('reference', '=', merchantReference)])
        success_url = transaction and "".join([success_url, '?txnId=', str(transaction.id)]) or success_url
        failed_url = transaction and "".join([failed_url, '?txnId=', str(transaction.id)]) or failed_url

        json_data = {
            "language": lang,
            'lineItems': lineItems,
            'currency': currency_name,
            'merchantReference': merchantReference,
            "successUrl": success_url,
            "failedUrl": failed_url,
        }

        billingAddress = values.get('billing_address', False)
        if billingAddress:
            json_data.update({'billingAddress': billingAddress})
        shippingAddress = values.get('shipping_address', False)
        if shippingAddress:
            json_data.update({'shippingAddress': shippingAddress})
        customerId = tx_details.get('partner_id', False)
        if customerId:
            json_data.update({'customerId': customerId})
        wallee_payment_method = values.get('wallee_payment_method', False)
        if wallee_payment_method:
            json_data.update({'allowedPaymentMethodConfigurations': [{'id': wallee_payment_method}]})

        response = wallee_acquirer.wallee_send_request(wallee_acquirer_id, \
                                                       type=type, uri=uri, \
                                                       json_data=json_data)
        status = response.get('status', 0)
        data = response.get('data', [])
        error = response.get('error', _('Error cant be retrived'))
        res = {}
        if status == 200 and data:
            res = {'trans_id': data['id']}
        else:
            res = {'trans_id': False, 'error': error}
        return res

    def cron_update_wallee_state(self):
        wallee_transactions = self.env['payment.transaction'].search([('acquirer_id.provider', '=', 'wallee'),
                                                                      ('acquirer_reference', '!=', False),
                                                                      '|',
                                                                      ('wallee_state', 'not in',
                                                                       ['FULFILL', 'DECLINE', 'FAILED']),
                                                                      ('state', 'not in', ['done', 'cancel', 'error'])])
        for tx in wallee_transactions:
            tx._process_feedback_data(data={'from_cron': True})
            tx_to_process = tx.filtered(lambda x: x.state == 'done' and x.is_post_processed is False)
            try:
                tx_to_process._finalize_post_processing()
            except Exception as e:
                self.env.cr.rollback()
                _logger.exception("Error while processing transaction(s) %s, exception \"%s\"", tx_to_process.ids,
                                  str(e))


class PaymentTransaction(models.Model):
    _name = 'payment.transaction'
    _inherit = ['payment.transaction', 'mail.thread']

    _wallee_pending_states = ['CREATE', 'PENDING', 'CONFIRMED', 'PROCESSING', 'AUTHORIZED', 'COMPLETED']

    wallee_state = fields.Char(string='Wallee State', readonly=True, track_visibility='onchange')
    pending_email_send = fields.Boolean(default=False)

    def _set_transaction_date(self):
        self.write({'last_state_change': datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)})

    def _get_specific_rendering_values(self, tx_values):
        res = super()._get_specific_rendering_values(tx_values)
        if self.provider != 'wallee':
            return res
        self.ensure_one()
        context = self._context or {}
        reference = tx_values.get('reference')
        wallee_payment_method = request.session.get('wallee_payment_method', {})
        trans_id = wallee_payment_method.get('trans_id', 0)
        method_id = wallee_payment_method.get('method_id', 0)
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        success_url = urls.url_join(base_url, WalleeController._success_url)
        failed_url = urls.url_join(base_url, WalleeController._failed_url)
        wallee_redirect_url = urls.url_join(base_url, WalleeController._wallee_redirect_url)
        tx_values.update({'wallee_tx_url': '',
                          'api_url': '',
                          'wallee_javascript_url': '',
                          'merchant': self.company_id.name,
                          'wallee_payment_method': method_id})
        Transaction = self.env['payment.transaction']
        transaction = Transaction.search([('reference', '=', reference)])
        success_url = transaction and "".join([success_url, '?txnId=', str(transaction.id)]) or success_url
        failed_url = transaction and "".join([failed_url, '?txnId=', str(transaction.id)]) or failed_url
        tx_values.update({'successUrl': success_url,
                          'failedUrl': failed_url})
        acquirer_reference = trans_id if trans_id else transaction.acquirer_reference
        wallee_tx_values = {}
        partner_first_name, partner_last_name = payment_utils.split_partner_name(self.partner_id.name)
        billing_address = {
            "city": self.partner_city if self.partner_city else "",
            "emailAddress": self.partner_email if self.partner_email else "",
            "givenName": partner_last_name if self.partner_id else "",
            "familyName": partner_first_name if self.partner_id else "",
            "phoneNumber": self.partner_phone if self.partner_phone else "",
            "organizationName": self.company_id.name if self.company_id else "",
            "postcode": self.partner_zip if self.partner_zip else "",
            "street": self.partner_address if self.partner_address else "",
            "state": self.partner_state_id.name if self.partner_state_id else "",
            "country": self.partner_country_id.code if self.partner_country_id else "",
            "postalState": self.partner_state_id.code if self.partner_state_id else "",
        }
        tx_values.update(billing_address)
        shipping_address = billing_address.copy()
        tx_details = {
            'currency_name': self.currency_id.name,
            'name': reference,
            'partner_id': tx_values.get('partner_id', ''),
        }
        tx_values.update(tx_details)
        txline_details = transaction.get_wallee_line_details()
        wallee_tx_values['wallee_payment_method'] = method_id
        wallee_tx_values['txline_details'] = txline_details
        wallee_tx_values['tx_details'] = tx_details
        wallee_tx_values['partner_id'] = self.partner_id.id
        wallee_tx_values['billing_address'] = billing_address
        wallee_tx_values['shipping_address'] = shipping_address
        wallee_state = ''
        wallee_version = False
        wallee_trans = {}
        Acquirer = self.env['payment.acquirer']
        walle_acquirer = Acquirer.search([('id', '=', tx_values.get('acquirer_id'))])
        tx_values.update({'acquirer_wallee': walle_acquirer.id})
        if acquirer_reference:
            search_params = {'acquirer_reference': acquirer_reference}
            response = Acquirer.wallee_search_transation_id(walle_acquirer.id, search_params)
            status = response.get('status', 0)
            data = response.get('data', [])
            if status == 200 and data:
                wallee_trans = data[0]
                wallee_state = wallee_trans.get('state', '')
                wallee_version = wallee_trans.get('version', '')
        if wallee_version and wallee_state in ['CREATE', 'PENDING']:
            search_params = {'acquirer_reference': trans_id, 'version': wallee_version}
            response = Acquirer.wallee_update_transation_id(walle_acquirer.id, search_params,
                                                            wallee_tx_values)  # To Do: handle the failure case in update transactions
        else:
            response = Acquirer.wallee_create_transation(walle_acquirer.id,
                                                         wallee_tx_values)  # To Do: handle the failure case in transactions
            acquirer_reference = response.get('trans_id', False)
        tx_url = context.get('tx_url', False)
        if acquirer_reference and wallee_payment_method and not tx_url:
            transaction_interface = wallee_payment_method.get('trans_interface', False)
            if transaction_interface == 'OFFSITE':
                response = Acquirer.wallee_build_payment_page_url(walle_acquirer.id, acquirer_reference)
                wallee_tx_url = response.get('wallee_redirect_url', False)
                tx_values['wallee_tx_url'] = wallee_tx_url
                tx_values['wallee_redirect_url'] = wallee_redirect_url
                tx_values['api_url'] = wallee_tx_url
            elif transaction_interface == 'ONSITE':
                response = Acquirer.wallee_build_javascript_url(walle_acquirer.id, acquirer_reference)
                wallee_javascript_url = response.get('wallee_javascript_url', False)
                tx_values['wallee_javascript_url'] = wallee_javascript_url
            request.session["wallee_payment_method"]['trans_id'] = acquirer_reference
            prev_trans = Transaction.search([
                ('id', 'not in', transaction.ids),
                ('acquirer_reference', '=', acquirer_reference),
                ('acquirer_id.provider', '=', 'wallee'),
                ('wallee_state', 'not in', ['FULFILL', 'DECLINE', 'FAILED']),
                ('state', 'in', ['draft'])
            ])
            prev_trans.write({'state': 'cancel'})
            transaction.write({'acquirer_reference': acquirer_reference})
        return tx_values

    @api.model
    def _get_tx_from_feedback_data(self, provider, data):
        """ Override of payment to find the transaction based on Wallee data.

        :param str provider: The provider of the acquirer that handled the transaction
        :param dict data: The feedback data sent by the provider
        :return: The transaction if found
        :rtype: recordset of `payment.transaction`
        :raise: ValidationError if inconsistent data were received
        :raise: ValidationError if the data match no transaction
        :raise: ValidationError if the signature can not be verified
        """
        tx = super()._get_tx_from_feedback_data(provider, data)
        if provider != 'wallee':
            return tx
        txn_id = data.get('txn_id', 0)
        if not txn_id:
            wallee_payment_method = request and request.session.get('wallee_payment_method', {}) or {}
            wallee_reference = wallee_payment_method.get('trans_id', 0)
            tx = self.search([
                ('id', '=', wallee_reference),
                ('acquirer_id.provider', '=', 'wallee'),
                ('wallee_state', 'not in', ['FULFILL', 'DECLINE', 'FAILED']),
                ('state', 'in', ['draft'])
                # ('state', 'not in', ['cancel'])
            ])
        else:
            tx_ids_list = self.search([('id', '=', txn_id)]).ids
            tx = self.browse(tx_ids_list)
        if not tx or len(tx) > 1:
            error_msg = _('Wallee: not received data for reference')
            if not tx:
                error_msg += _('; no order found')
            else:
                error_msg += _('; multiple order found')
            _logger.info(error_msg)
            raise ValidationError(error_msg)
        return tx[0]

    def _process_feedback_data(self, data):
        """ Override of payment to process the transaction based on Buckaroo data.

        Note: self.ensure_one()

        :param dict data: The feedback data sent by the provider
        :return: None
        :raise: ValidationError if inconsistent data were received
        """
        super()._process_feedback_data(data)
        self.ensure_one()
        if self.provider != 'wallee':
            return
        search_params = {'acquirer_reference': self.acquirer_reference}
        wallee_acquirer = self.acquirer_id
        res = False
        try:
            self._cr.execute("SELECT 1 FROM payment_transaction WHERE id = %s FOR UPDATE NOWAIT", [self.id],
                             log_exceptions=False)
            response = wallee_acquirer.wallee_search_transation_id(wallee_acquirer.id, search_params)
            status = response.get('status', 0)
            res_data = response.get('data', [])
            error = response.get('error', _('Error cant be retrived'))
            error = response.get('error', '')
            wallee_state = ''
            if status == 200 and res_data:
                wallee_trans = res_data[0]
                wallee_state = wallee_trans.get('state', '')
                from_cron = data.get('from_cron', False)
                if from_cron and not self.wallee_state and wallee_state in self._wallee_pending_states or self.wallee_state in self._wallee_pending_states and wallee_state in self._wallee_pending_states or self.wallee_state == wallee_state:
                    self.write({'wallee_state': wallee_state})
                    return True;
                self.write({'wallee_state': wallee_state})
            if wallee_state in self._wallee_pending_states:
                if self.state != 'pending':
                    self._set_transaction_date()
                    self._set_pending()
                    if self.acquirer_id.send_status_email and not self.pending_email_send:
                        try:
                            template_id = self.env.ref(
                                'payment_wallee.wallee_email_template_payment_transaction_pending')
                            if template_id:
                                template_id.send_mail(self.id, force_send=True)
                                self.write({'pending_email_send': True})
                        except Exception as e:
                            _logger.info("Error! email cannot be send %s" % (e,))
                res = True
            # elif wallee_state == 'AUTHORIZED':
            #     self._set_transaction_date()
            #     res = True
            elif wallee_state == 'FULFILL':
                self._set_done()
                if self.acquirer_id.send_status_email:
                    try:
                        template_id = self.env.ref('payment_wallee.wallee_email_template_payment_transaction_confirmed')
                        if template_id:
                            template_id.send_mail(self.id, force_send=True)
                    except Exception as e:
                        _logger.info("Error! email cannot be send %s" % (e,))
                res = True
            # elif wallee_state == 'PENDING':
            #     self._set_pending()
            #     res = True
            elif wallee_state in ['FAILED', 'DECLINE']:
                self._set_canceled()
                if self.acquirer_id.send_status_email:
                    try:
                        template_id = self.env.ref('payment_wallee.wallee_email_template_payment_transaction_cancelled')
                        if template_id:
                            template_id.send_mail(self.id, force_send=True)
                    except Exception as e:
                        _logger.info("Error! email cannot be send %s" % (e,))
                res = False
            else:
                error = _('Wallee: feedback error')
                _logger.info(error)
                # self._set_error(error)
                self.write({'state_message': error})
                self._set_transaction_date()
                res = True
        except OperationalError as e:
            _logger.info("A pgOperationalError occured while processing _wallee_form_validate: %s", e.pgerror)
            if e.pgcode == '55P03':
                pass
            else:
                raise
        except Error as e:
            _logger.info("A pgError occured while _processing _wallee_form_validate: %s", e.pgerror)
            raise
        except Exception as e:
            _logger.info("An Error occured while processing _wallee_form_validate: %s" % (e,))
            raise
        return res

    def get_wallee_line_details(self):
        self.ensure_one()
        line_details = []
        invoice_ids = self.invoice_ids.mapped('id')
        if invoice_ids:
            for line in self.env['account.move'].sudo().browse(invoice_ids).invoice_line_ids:
                line_details.append({
                    'name': line.name[:140],
                    'quantity': line.quantity,
                    'shippingRequired': "false",
                    'sku': line.product_id.default_code,
                    "type": "PRODUCT",
                    "uniqueId": line.product_id.id,
                    "amountIncludingTax": round(line.price_total, 2)
                })
        sale_order_ids = self.sale_order_ids.mapped('id')
        if not line_details and sale_order_ids:
            orderline_details = self.env['sale.order.line'].sudo().search([('order_id', 'in', sale_order_ids)])
            for line in orderline_details:
                line_details.append({
                    'name': line.name[:140],
                    'quantity': line.product_uom_qty,
                    'shippingRequired': "false",
                    'sku': line.product_id.default_code,
                    "type": "PRODUCT",
                    "uniqueId": line.product_id.id,
                    "amountIncludingTax": line.price_total,
                })
        if not line_details:
            line_details.append({
                'name': _("Total"),
                'quantity': 1,
                "type": "PRODUCT",
                "uniqueId": _("total"),
                "amountIncludingTax": self.amount,
            })
        return line_details

# class IrUiView(models.Model):
#     _inherit = 'ir.ui.view'
#
#     def _render(self, values=None, engine='ir.qweb', minimal_qcontext=False):
#         context = self._context or {}
#         ctxt_tx_url = context.get('tx_url', False)
#         if values and values.get('wallee_tx_url', False) and values.get('wallee_redirect_url',
#                                                                         False) and not ctxt_tx_url:
#             values['tx_url'] = values['wallee_redirect_url']
#         return super(IrUiView, self)._render(values=values, engine=engine, minimal_qcontext=minimal_qcontext)
