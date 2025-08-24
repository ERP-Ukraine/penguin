# -*- coding: utf-8 -*-
#################################################################################
# Author      : PIT Solutions AG. (<https://www.pitsolutions.com/>)
# Copyright(c): 2019 - Present PIT Solutions AG.
# License URL : https://www.webshopextension.com/en/licence-agreement/
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <https://www.webshopextension.com/en/licence-agreement/>
#################################################################################

import base64
import logging
from io import BytesIO
from datetime import datetime, date
from dateutil import relativedelta

import cairosvg
import requests
from PIL import Image
from wallee import Configuration
from wallee.api import (
    PaymentMethodConfigurationServiceApi,
    TransactionServiceApi,
    TransactionIframeServiceApi,
    TransactionLightboxServiceApi,
    RefundServiceApi
)
from wallee.models import (
    TransactionCreate,
    EntityQueryFilter,
    EntityQueryFilterType,
    CriteriaOperator,
)
from werkzeug import urls

from odoo import api, models, fields, _
from odoo.exceptions import ValidationError
from odoo.http import request
from odoo.tools.float_utils import float_repr
from ..constants import (
    WALLEE_OPERATIONS,
    WALLEE_INTERFACE_TYPES,
)
from ..controllers.main import WalleeController

_logger = logging.getLogger(__name__)


class PaymentProvider(models.Model):
    _inherit = 'payment.provider'

    code = fields.Selection(
        selection_add=[('wallee', "Wallee")],
        ondelete={'wallee': 'set default'}
    )
    wallee_api_userid = fields.Integer(
        required_if_provider='wallee', string='UserID',
        groups='base.group_system',
        help="The Wallee user ID for API authentication"
    )
    wallee_api_spaceid = fields.Integer(
        required_if_provider='wallee', string='Space ID',
        groups='base.group_system',
        help="The Wallee space ID for API operations"
    )
    wallee_api_application_key = fields.Char(
        required_if_provider='wallee', string='Application Key',
        groups='base.group_system',
        help="The Wallee application key for API authentication"
    )
    wallee_method_ids = fields.One2many(
        'wallee.payment.method', 'acquirer_id', 'Supported Wallee Payment Methods'
    )
    hide_registration_templ = fields.Boolean(
        'Hide S2S Form Template', compute='_compute_wallee_feature_support', store=True
    )
    hide_specific_countries = fields.Boolean(
        compute='_compute_wallee_feature_support', store=True
    )
    hide_payment_method_ids = fields.Boolean(
        'Hide Payment Icons', compute='_compute_wallee_feature_support', store=True
    )
    hide_env_button = fields.Boolean(
        compute='_compute_wallee_feature_support', store=True
    )
    send_status_email = fields.Boolean(default=True)
    payment_page = fields.Selection(
        WALLEE_INTERFACE_TYPES,
        default='iframe'
    )

    # Operation type mapping for user-friendly logging
    OPERATION_DESCRIPTIONS = {
        'search_transaction': 'Search Transaction',
        'create_transaction': 'Create Transaction',
        'update_transaction': 'Update Transaction',
        'fetch_payment_methods': 'Fetch Payment Methods',
        'refund_transaction': 'Refund Transaction',
        'void_transaction': 'Void Transaction'
    }

    def _get_feature_support(self):
        return {}.fromkeys(["hide_registration_templ", "hide_specific_countries",
                            "hide_payment_method_ids", "hide_env_button"], ["wallee"])

    @api.depends('code')
    def _compute_wallee_feature_support(self):
        feature_support = self._get_feature_support()
        for acquirer in self:
            acquirer.hide_registration_templ = acquirer.code in feature_support.get('hide_registration_templ', [])
            acquirer.hide_specific_countries = acquirer.code in feature_support.get('hide_specific_countries', [])
            acquirer.hide_payment_method_ids = acquirer.code in feature_support.get('hide_payment_method_ids', [])
            acquirer.hide_env_button = acquirer.code in feature_support.get('hide_env_button', [])

    def _compute_feature_support_fields(self):
        """ Override of `payment` to enable additional features. """
        super()._compute_feature_support_fields()
        self.filtered(lambda p: p.code == 'wallee').update({
            'support_refund': 'full_only',
        })

    def _check_and_update_payment_methods(self, vals):
        keys_to_check = ['wallee_api_userid', 'wallee_api_spaceid', 'wallee_api_application_key']
        if any(key in vals for key in keys_to_check):
            self.update_wallee_payment_methods()

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        for vals in vals_list:
            self._check_and_update_payment_methods(vals)
        return res

    def write(self, values):
        res = super().write(values)
        self._check_and_update_payment_methods(values)
        return res

    def copy(self, default=None):
        default = dict(default or {})
        default.setdefault('name', _("%(old_name)s (copy)", old_name=self.name))
        return super().copy(default=default)

    @api.onchange('state', 'website_id', 'wallee_api_spaceid')
    def check_existing_wallee_provider_for_website(self):
        for record in self:
            if record.code == 'wallee' and record.state in ['test', 'enabled'] and record.wallee_api_spaceid:
                active_wallee_providers = self.search([
                    ('code', '=', 'wallee'),
                    ('wallee_api_spaceid', '=', record.wallee_api_spaceid),
                    ('state', 'in', ['test', 'enabled']),
                    ('id', 'not in', record._origin.ids)
                ])
                # list of id of websites for which there is already a provider configured with this space id
                mapped_websites = active_wallee_providers.mapped('website_id').ids
                if record.website_id and record.website_id.id in mapped_websites:
                    # Raise a warning if a provider with the same Website and Space ID already exists when attempting to configure a new one.
                    raise ValidationError(
                        _("A provider with the same Website and Space ID already exists. Please use a different Space ID or modify the existing configuration.!"))
                if active_wallee_providers and ((not record.website_id) or any(
                        not provider.website_id for provider in active_wallee_providers
                )):
                    # Raise a warning if the user attempts to configure a provider under the following conditions:
                    # 1. A provider with the same Space ID already exists, but without an associated website. This can result in duplicate payment methods on the checkout page.
                    # 2. The current provider configuration is being set up without linking to a website.
                    raise ValidationError(_(
                        "You cannot configure a wallee provider using this Space ID without associating it with a Website. This Space ID is already linked to another provider."
                    ))

    # send request with key
    @api.model
    def _wallee_send_request(self, operation_type, json_data=None, **kwargs):
        """Send request to Wallee API.

        Args:
            operation_type (str): Type of operation to perform (e.g., 'search_transaction')
            json_data (dict): Data to send with the request
            **kwargs: Additional parameters for the operation
        """
        provider_log = self.env['payment.provider.log'].sudo()
        self.ensure_one()
        if not self.wallee_api_userid or not self.wallee_api_spaceid or not self.wallee_api_application_key:
            raise ValidationError(_('Wallee: Missing API credentials'))

        operation = WALLEE_OPERATIONS.get(operation_type)
        if not operation:
            raise ValidationError(_('Wallee: Invalid operation type %s', operation_type))

        try:
            # Initialize configuration and service
            space_id = self.wallee_api_spaceid
            configuration = Configuration(
                user_id=self.wallee_api_userid,
                api_secret=self.wallee_api_application_key
            )
            transaction_service = TransactionServiceApi(configuration)

            # Handle different operation types
            response = None
            if operation_type == 'search_transaction':
                response = transaction_service.search(space_id, json_data)
            elif operation_type == 'create_transaction':
                response = transaction_service.create(space_id, json_data)
            elif operation_type == 'update_transaction':
                response = transaction_service.update(space_id, json_data)
            elif operation_type == 'fetch_payment_methods':
                transaction_id = kwargs.get('transaction_id')
                if not transaction_id:
                    raise ValidationError(_('Wallee: Missing transaction ID for fetching payment methods'))
                response = transaction_service.fetch_payment_methods(space_id, transaction_id, self.payment_page)

            # Serialize response for logging
            serialized_response = self._serialize_wallee_response(response)

            # Get user-friendly operation name
            operation_name = self.OPERATION_DESCRIPTIONS.get(operation_type, operation_type)

            # Log successful response
            provider_log._post_log({
                'name': '200',
                'description': f'Successful {operation_name}',
                'response_data': provider_log._format_response(serialized_response),
                'provider_id': self.id,
                'source': 'ecommerce'
            })

            return {
                'status': 200,
                'data': response
            }

        except Exception as e:
            error_message = str(e)
            _logger.error("Unexpected error in Wallee request: %s", error_message)

            # Get user-friendly operation name
            operation_name = self.OPERATION_DESCRIPTIONS.get(operation_type, operation_type)

            # Log error response
            provider_log._post_log({
                'name': '500',
                'description': f'Failed {operation_name}',
                'response_data': provider_log._format_response({
                    'error': error_message,
                    'operation': operation_name,
                    'request_data': json_data
                }),
                'provider_id': self.id,
                'source': 'ecommerce'
            })

            return {
                'status': 500,
                'error': error_message
            }

    def _serialize_wallee_response(self, response):
        """Convert Wallee SDK response objects to serializable format."""
        if hasattr(response, 'to_dict'):
            return response.to_dict()
        elif isinstance(response, (list, tuple)):
            return [self._serialize_wallee_response(item) for item in response]
        elif isinstance(response, dict):
            return {k: self._serialize_wallee_response(v) for k, v in response.items()}
        elif isinstance(response, datetime):
            return fields.Datetime.to_string(response)
        elif isinstance(response, date):
            return fields.Date.to_string(response)
        return response

    @api.model
    def get_available_wallee_payment_methods(self):
        # Initialize Wallee SDK
        config = Configuration(
            user_id=self.sudo().wallee_api_userid, api_secret=self.sudo().wallee_api_application_key
        )
        space_id = self.sudo().wallee_api_spaceid
        payment_method_configuration_service = PaymentMethodConfigurationServiceApi(config)
        try:
            # Search for payment method configurations
            query = {}  # Create an empty query
            response = payment_method_configuration_service.search(space_id=space_id, query=query)
            wallee_payment_methods = []
            for pay_method in response:
                one_click_payment_mode = pay_method.one_click_payment_mode.value
                values = {
                    'name': pay_method.name,
                    'sequence': pay_method.sort_order,
                    'acquirer_id': self.id,
                    'space_id': pay_method.space_id,
                    'method_id': pay_method.id,
                    'image_url': pay_method.resolved_image_url,
                    'one_click': 1 if one_click_payment_mode == 'ALLOW' else 0,
                    'one_click_mode': one_click_payment_mode,
                    'payment_method_ref': pay_method.payment_method,
                    'transaction_interface': pay_method.data_collection_type,
                    'active': pay_method.state.value == 'ACTIVE',
                    'version': pay_method.version,
                }
                wallee_payment_methods.append(values)
            return wallee_payment_methods
        except Exception as e:
            _logger.exception("Error fetching Wallee payment methods: %s", e)
            return []

    @api.model
    def get_available_wallee_trans_payment_methods(
            self, currency_name, amount, origin, billing_partner_id, access_token, transaction_source
    ):
        """Get available payment methods for a Wallee transaction.

        Uses model-based state management instead of session to track transactions.
        Attempts to reuse existing transactions when possible.
        Only creates new transactions when necessary.
        """
        # Validate source transaction
        if transaction_source._name == 'account.move' and transaction_source.amount_total != transaction_source.amount_residual:
            return {}
        if not currency_name or amount <= 0.0 or not origin:
            return self.get_available_wallee_payment_methods()

        try:
            space_id = self.sudo().wallee_api_spaceid
            # Get origin from access token if needed
            origin = self._get_origin_from_access_token(origin, access_token)

            # Prepare transaction details
            tx_details = {
                'currency_name': currency_name,
                'name': origin,  # Use actual reference
                'amount': amount
            }

            # Prepare line items and billing address
            txline_details = self._prepare_transaction_line_details(amount)
            billing_address = self._get_billing_address(billing_partner_id)

            # Try to reuse or create transaction
            trans_id = self._handle_wallee_transaction(
                currency_name,
                {
                    'tx_details': tx_details,
                    'txline_details': txline_details,
                    'billing_address': billing_address
                }
            )

            if not trans_id:
                _logger.error("Failed to handle Wallee transaction")
                return {}

            # Store transaction ID in source model if possible
            if hasattr(transaction_source, 'provider_reference') and not transaction_source.provider_reference:
                transaction_source.write({'provider_reference': trans_id})
                _logger.info("Updated source transaction with Wallee reference: %s", trans_id)

            # Get available payment methods
            return self._fetch_payment_methods(space_id, trans_id)

        except Exception as e:
            _logger.error("Failed to get Wallee payment methods: %s", str(e))
            return {}

    def update_wallee_payment_methods(self):
        """Update Wallee payment methods for the current acquirer.

        Fetches available payment methods from Wallee API, creates/updates
        corresponding payment.method records, and deactivates unused methods.
        """
        payment_method_obj = self.env['payment.method']

        for acquirer in self:
            try:
                # Clear existing methods
                acquirer.wallee_method_ids.unlink()

                # Fetch available methods from Wallee
                wallee_methods = acquirer.get_available_wallee_payment_methods()
                if not wallee_methods:
                    continue

                # Process active methods
                self._process_active_payment_methods(acquirer, payment_method_obj, wallee_methods)

                # Deactivate unused methods
                self._deactivate_unused_payment_methods(acquirer, payment_method_obj, wallee_methods)

            except Exception as e:
                _logger.error("Failed to update Wallee payment methods for acquirer %s: %s", acquirer.id, str(e))
                raise

    @api.model
    def get_non_wallee_acquirers(self, acquirers, website_id):
        return [acq for acq in acquirers if
                acq.code != 'wallee' and (acq.website_id == website_id or not acq.website_id)]

    @api.model
    def get_wallee_acquirers(self, acquirers, website_id):
        return [acq for acq in acquirers if
                acq.code == 'wallee' and (acq.website_id == website_id or not acq.website_id)]

    @api.model
    def wallee_build_payment_page_url(self, trans_id):
        response = self._wallee_send_request(operation_type='fetch_payment_methods', transaction_id=trans_id)
        data = response.get('data', [])
        if response.get('status', 0) == 200 and data:
            return {
                'wallee_redirect_url': data
            }
        return {
            'wallee_redirect_url': False,
            'error': response.get('error', _("Error can't be retrieved in wallee_build_payment_page_url"))
        }

    @api.model
    def wallee_build_javascript_url(self, trans_id):
        payment_page = self.sudo().payment_page
        try:
            # Initialize Wallee SDK
            config = Configuration(
                user_id=self.sudo().wallee_api_userid,
                api_secret=self.sudo().wallee_api_application_key
            )
            space_id = self.sudo().wallee_api_spaceid
            if payment_page == 'iframe':
                # Use TransactionIframeService for iframe
                iframe_service = TransactionIframeServiceApi(config)
                javascript_url = iframe_service.javascript_url(space_id=space_id, id=trans_id)
                return {'wallee_javascript_url': javascript_url}
            else:
                # Use TransactionLightboxService for lightbox
                lightbox_service = TransactionLightboxServiceApi(config)
                javascript_url = lightbox_service.javascript_url(space_id=space_id, id=trans_id)
                return {'wallee_lightbox_javascript_url': javascript_url}
        except Exception as e:
            _logger.exception("Error building Wallee JavaScript URL: %s", str(e))
            if payment_page == 'iframe':
                return {
                    'wallee_javascript_url': False,
                    'error': str(e)
                }
            else:
                return {
                    'wallee_lightbox_javascript_url': False,
                    'error': str(e)
                }

    @api.model
    def wallee_search_transaction_id(self, search_params):
        """Search for a transaction by ID using wallee_send_request.

        Args:
            search_params (dict): Search parameters, including 'provider_reference'.

        Returns:
            dict: Search results
        """
        return self._wallee_send_request(operation_type='search_transaction', json_data=search_params)

    @api.model
    def wallee_update_transaction(self, transaction_id, values):
        """Update transaction details in Wallee platform.

        Args:
            transaction_id (int): ID of the transaction to update
            values (dict): Contains transaction details like 'tx_details', 'txline_details', addresses, etc.

        Returns:
            dict: Result from wallee_send_request.
        """

        try:
            lang = self._get_user_language()
            base_url = self.get_base_url()
            success_url = urls.url_join(base_url, WalleeController._success_url)
            failed_url = urls.url_join(base_url, WalleeController._failed_url)
            tx_details = values.get('tx_details')
            merchant_reference = tx_details.get('name', '')
            transaction = self.env['payment.transaction'].search([('reference', '=', merchant_reference)], limit=1)
            success_url = f"{success_url}?txnId={transaction.id}" if transaction else success_url
            failed_url = f"{failed_url}?txnId={transaction.id}" if transaction else failed_url

            json_data = {
                'id': transaction_id,
                "language": lang,
                'lineItems': values.get('txline_details', []),
                'currency': tx_details.get('currency_name', ''),
                'merchantReference': merchant_reference,
                "successUrl": success_url,
                "failedUrl": failed_url,
                "version": 1,
            }

            billing_address = values.get('billing_address', False)
            if billing_address:
                json_data.update({'billingAddress': billing_address})
            shipping_address = values.get('shipping_address', False)
            if shipping_address:
                json_data.update({'shippingAddress': shipping_address})
            wallee_payment_method = values.get('wallee_payment_method', False)
            if wallee_payment_method:
                json_data.update({'allowedPaymentMethodConfigurations': [{'id': wallee_payment_method}]})
            else:
                json_data.update({'allowedPaymentMethodConfigurations': []})

            result = self._wallee_send_request(
                operation_type='update_transaction',json_data=json_data
            )

            if result.get('status') == 200:
                _logger.info("Successfully updated Wallee transaction %s name to %s", values.get('id', ''), values.get('name', ''))
                return True

            _logger.error("Failed to update Wallee transaction %s name", values.get('id', ''))
            return False

        except Exception as e:
            _logger.error("Failed to update Wallee transaction: %s", str(e))
            return False

    @api.model
    def wallee_create_transaction(self, values):
        """Create a transaction in Wallee payment system.

        This method first checks for existing transactions and updates them if found.
        Otherwise, it creates a new transaction in the Wallee system.
        """
        # Check for existing transaction and return it if found
        existing_transaction = self._get_existing_wallee_transaction(values)
        if existing_transaction:
            return existing_transaction

        # If no existing transaction found, create a new one
        config = self._prepare_wallee_config()
        space_id = self.sudo().wallee_api_spaceid
        transaction_service = TransactionServiceApi(config)

        # Prepare transaction data
        transaction = self._prepare_wallee_transaction_data(values)

        if not values.get('merchant_reference') and transaction.merchant_reference:
            values['merchant_reference'] = transaction.merchant_reference
        # Set success/failed URLs if not in terminal context
        if not self.env.context.get('wallee_terminal', False):
            self._set_wallee_transaction_urls(transaction, values)

        # Create the transaction
        return self._execute_wallee_transaction_creation(transaction_service, space_id, transaction)

    def _get_existing_wallee_transaction(self, values):
        """Check if there's an existing transaction and return it if found."""
        transaction_record = self.env['payment.transaction'].search(
            [('reference', '=', values.get('merchant_reference'))], limit=1)

        if not (transaction_record and transaction_record.provider_reference):
            return None

        # Try to find existing Wallee transaction
        search_params = {'provider_reference': transaction_record.provider_reference}
        existing_wallee_trans = self.wallee_search_transaction_id(search_params)

        if not (existing_wallee_trans and existing_wallee_trans.get('items')):
            return None

        # Update existing transaction name if needed
        trans_id = existing_wallee_trans['items'][0].get('id')
        if trans_id:
            self.wallee_update_transaction(trans_id, {'tx_details': {'name': values.get('merchant_reference', '')}})
            return existing_wallee_trans['items'][0]

        return None

    def _prepare_wallee_config(self):
        """Prepare Wallee API configuration."""
        return Configuration(
            user_id=self.sudo().wallee_api_userid,
            api_secret=self.sudo().wallee_api_application_key
        )

    def _prepare_wallee_transaction_data(self, values):
        """Prepare the transaction data for Wallee API."""
        transaction = TransactionCreate(
            currency=values.get('tx_details', {}).get('currency_name', ''),
            merchant_reference=values.get('tx_details', {}).get('name', ''),
            customer_id=values.get('tx_details', {}).get('partner_id', False),
            language=self._get_user_language()
        )

        # Add line items to the transaction
        transaction.line_items = values.get('txline_details', [])

        # Add billing and shipping addresses
        if values.get('billing_address', False):
            transaction.billing_address = values.get('billing_address', False)
        if values.get('shipping_address', False):
            transaction.shipping_address = values.get('shipping_address', False)

        return transaction

    def _set_wallee_transaction_urls(self, transaction, values):
        """Set success and failed URLs for the transaction."""
        base_url = self.get_base_url()
        success_url = urls.url_join(base_url, WalleeController._success_url)
        failed_url = urls.url_join(base_url, WalleeController._failed_url)

        transaction_record = self.env['payment.transaction'].search(
            [('reference', '=', values.get('merchant_reference'))], limit=1)

        if transaction_record:
            success_url = f"{success_url}?txnId={transaction_record.id}"
            failed_url = f"{failed_url}?txnId={transaction_record.id}"

        transaction.success_url = success_url
        transaction.failed_url = failed_url

        if values.get('wallee_payment_method', False):
            transaction.allowed_payment_method_configurations = [{'id': values.get('wallee_payment_method')}]

    def _execute_wallee_transaction_creation(self, transaction_service, space_id, transaction):
        """Execute the transaction creation in Wallee and handle the response."""
        try:
            # Create the transaction
            transaction_create = transaction_service.create(space_id=space_id, transaction=transaction)
            return {
                'trans_id': transaction_create.id
            }
        except Exception as e:
            _logger.exception("Error creating Wallee transaction: %s", e)
            return {
                'trans_id': False,
                'error': _("Error creating Wallee transaction: %s", e)
            }

    def action_view_wallee_payment_methods(self):
        self.ensure_one()
        self.update_wallee_payment_methods()
        action = self.env.ref('payment_wallee.action_wallee_payment_method').read()[0]
        action['domain'] = [('acquirer_id', '=', self.id),('space_id', '=', self.wallee_api_spaceid)]
        return action

    def action_create_wallee_payment_provider(self):
        wallee_providers_count = self.search_count([('code', '=', 'wallee')])
        view_id = self.env.ref('payment_wallee.redirect_form').id
        if view_id:
            new_wallee_provider = self.create({
                'name': f'Wallee Payment Providers ({wallee_providers_count + 1})',
                'code': 'wallee',
                'state': 'disabled',
                'wallee_api_userid': '1234',
                'wallee_api_spaceid': '1234',
                'wallee_api_application_key': 'dummy',
                'redirect_form_view_id': view_id,
                'image_128': self.image_128,
                'module_id': self.module_id and self.module_id.id or False,
            })
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'payment.provider',
                'res_id': new_wallee_provider.id,
                'view_mode': 'form',
                'view_type': 'form',
                'target': 'current',
            }

    def cron_update_wallee_state(self):
        # Don't try forever to post-process a transaction that doesn't go through. Set the limit
        # to 4 days because some providers (PayPal) need that much for the payment verification.
        retry_limit_date = datetime.now() - relativedelta.relativedelta(days=4)
        # Retrieve all transactions matching the criteria for post-processing
        wallee_transactions = self.env['payment.transaction'].search([
            ('last_state_change', '>=', retry_limit_date),
            ('provider_id.code', '=', 'wallee'),
            ('provider_reference', '!=', False),
            '|',
            ('wallee_state', 'not in',
             ['FULFILL', 'DECLINE', 'FAILED']),
            ('state', 'not in', ['done', 'cancel', 'error'])])
        for transaction in wallee_transactions:
            transaction._process_notification_data({'from_cron': True})
            tx_to_process = transaction.filtered(lambda x: x.state == 'done' and not x.is_post_processed)
            try:
                tx_to_process._post_process()
            except Exception as e:
                self.env.cr.rollback()
                _logger.exception("Error while processing transaction(s): %s: \nException %s", tx_to_process.ids, e)
            if len(wallee_transactions) > 1:
                self.env.ref('payment_wallee.cron_update_lastest_wallee_state')._trigger()
                return

    def cron_update_wallee_refund_state(self):
        wallee_refunds = self.env['payment.transaction'].search(
            [('provider_id.code', '=', 'wallee'),
             ('is_wallee_refund', '=', True),
             ('wallee_state', 'in', ['CREATE', 'SCHEDULED', 'MANUAL_CHECK', 'PENDING'])])
        for tx in wallee_refunds:
            tx.wallee_refund_form_validate()

    def cron_synchronize_payment_method_values(self):
        for acquirer in self.search([('code', '=', 'wallee'), ('state', '=', 'enabled')]):
            acquirer.update_wallee_payment_methods()

    def _get_origin_from_access_token(self, origin, access_token):
        """Get origin from access token if not provided."""
        if not origin and access_token:
            invoice = self.env['account.move'].sudo().search([('access_token', '=', access_token)], limit=1)
            origin = invoice.name if invoice else ''
        return origin

    def _prepare_transaction_details(self, currency_name, origin):
        """Prepare transaction details."""
        return {
            'currency_name': currency_name,
            'name': origin
        }

    def _prepare_transaction_line_details(self, amount):
        """Prepare transaction line details."""
        return [{
            'name': _("Total"),
            'quantity': 1,
            'type': "PRODUCT",
            'uniqueId': _("total"),
            'amountIncludingTax': float_repr(amount, 2)
        }]

    def _get_billing_address(self, billing_partner_id):
        """Get billing address from partner."""
        if billing_partner_id:
            billing_partner = self.env['res.partner'].browse(int(billing_partner_id))
            return self.env['payment.transaction'].get_partner_address(billing_partner)
        return {}

    def _handle_wallee_transaction(self, currency_name, data):
        """Handle Wallee transaction creation or update.
        First checks if a transaction already exists with the same reference.
        """
        try:
            tx_details = data.get('tx_details', {})
            reference = tx_details.get('name')  # This should be the origin/reference

            # Check if transaction already exists in Wallee using EntityQueryFilter
            if reference:
                # Use the base reference without any suffix
                base_reference = reference.split('-')[0]
                query_filter = self._create_entity_query_filter('merchantReference', base_reference)

                existing_tx = self._wallee_send_request(
                    'search_transaction',
                    {
                        'filter': query_filter,
                        'orderBys': [{
                            'fieldName': 'id',
                            'sorting': 'DESC'
                        }]
                    }
                )

                if existing_tx and existing_tx.get('status') == 200 and existing_tx.get('data'):
                    existing_tx = existing_tx['data'][0]
                    tx_state = existing_tx.state.value
                    _logger.info("Found existing Wallee transaction with reference %s in state %s",
                               reference, tx_state)

                    # Only reuse transaction if it's in a valid state
                    if tx_state in ['CREATE', 'PENDING']:
                        transaction_id = existing_tx.id
                        # Update currency if needed
                        if existing_tx.currency != currency_name:
                            _logger.info("Updating currency for transaction %s", transaction_id)
                            self._wallee_send_request(
                                'update_transaction',
                                {
                                    'id': transaction_id,
                                    'version': existing_tx.version,
                                    'currency': currency_name
                                }
                            )
                        return transaction_id
                    else:
                        _logger.info("Cannot reuse transaction with reference %s in state %s",
                                   reference, tx_state)

            # If no existing transaction or not reusable, create a new one
            tx_details = data.get('tx_details', {})
            txline_details = data.get('txline_details', [])
            billing_address = data.get('billing_address', {})

            # Create transaction
            transaction = self.wallee_create_transaction({
                'tx_details': tx_details,
                'txline_details': txline_details,
                'billing_address': billing_address
            })

            if transaction and transaction.get('trans_id'):
                return transaction['trans_id']

        except Exception as e:
            _logger.error("Failed to handle Wallee transaction: %s", str(e))

        return None

    def _fetch_payment_methods(self, space_id, trans_id):
        """Fetch available payment methods from Wallee using the SDK.

        Args:
            space_id (int): Wallee space ID
            trans_id (int): Transaction ID

        Returns:
            list: Available payment methods
        """
        provider_log = self.env['payment.provider.log'].sudo()
        try:
            # Initialize Wallee SDK configuration
            config = Configuration(
                user_id=self.sudo().wallee_api_userid,
                api_secret=self.sudo().wallee_api_application_key
            )

            # Create service instance
            transaction_service = TransactionServiceApi(config)

            # Fetch payment methods
            methods = transaction_service.fetch_payment_methods(space_id, trans_id, self.payment_page)

            # Log successful fetch
            provider_log._post_log({
                'name': '200',
                'description': f'Fetch Payment Methods - Transaction {trans_id}',
                'response_data': provider_log._format_response({
                    'methods_count': len(methods) if methods else 0,
                    'space_id': space_id,
                    'transaction_id': trans_id
                }),
                'provider_id': self.id,
                'source': 'ecommerce'
            })

            if not methods:
                return []

            # Process results
            lang = self._get_user_language()
            wallee_payment_methods = []

            for method in methods:
                name, description = self._get_method_name_and_description(method, lang)
                values = {
                    'name': name,
                    'description': description,
                    'sequence': method.sort_order,
                    'acquirer_id': self.id,
                    'space_id': method.space_id,
                    'method_id': method.id,
                    'image_url': method.resolved_image_url,
                    'one_click': 1 if method.one_click_payment_mode == 'ALLOW' else 0,
                    'one_click_mode': method.one_click_payment_mode,
                    'payment_method_ref': method.payment_method,
                    'transaction_interface': method.data_collection_type,
                    'trans_id': trans_id,
                    'active': method.state == 'ACTIVE',
                    'version': method.version,
                }
                wallee_payment_methods.append(values)

            return wallee_payment_methods

        except Exception as e:
            error_message = str(e)
            _logger.error('Failed to fetch Wallee payment methods: %s', error_message)

            # Log error
            provider_log._post_log({
                'name': '500',
                'description': f'Failed to Fetch Payment Methods - Transaction {trans_id}',
                'response_data': provider_log._format_response({
                    'error': error_message,
                    'space_id': space_id,
                    'transaction_id': trans_id
                }),
                'provider_id': self.id,
                'source': 'ecommerce'
            })
            return []

    def _get_user_language(self):
        """Get user's language code."""
        lang = 'en_US'
        if request:
            try:
                lang = request.lang.code or 'en_US'
            except Exception:
                lang = self.env.user.lang or 'en_US'
        return lang.replace('_', '-')

    def _get_method_name_and_description(self, pay_method, lang):
        """Get payment method name and description in user's language."""
        resolved_title = pay_method.resolved_title
        resolved_description = pay_method.resolved_description
        name = resolved_title.get(lang, False)
        description = resolved_description.get(lang, name)
        if not name or not description:
            tar_lang = lang.split('-')[0]
            for lang_code, transl_title in resolved_title.items():
                match_lang = lang_code.split('-')[0]
                if match_lang == tar_lang:
                    name = resolved_title.get(lang_code, name)
                    description = resolved_description.get(lang_code, name)
        return name, description

    def _process_active_payment_methods(self, acquirer, payment_method_obj, wallee_methods):
        """Process and update active payment methods."""
        active_codes = [str(method.get('method_id', '')) for method in wallee_methods]
        active_methods = payment_method_obj.with_context(active_test=False).search([
            ('is_wallee', '=', True),
            ('code', 'in', active_codes),
            ('provider_ids', 'in', acquirer.id)
        ])

        active_methods_dict = {method.code: method for method in active_methods}

        for method_data in wallee_methods:
            method_id = str(method_data.get('method_id', ''))
            method_name = method_data.get('name', '')
            method_image = self._read_image_file(method_data.get('image_url', False), output_format='JPEG')

            method = active_methods_dict.get(method_id)
            if method:
                self._update_existing_payment_method(method, method_name, method_image)
            else:
                method = self._create_new_payment_method(
                    acquirer, payment_method_obj, method_id, method_name, method_image
                )

            method_data['name'] = method.id
            self.env['wallee.payment.method'].create(method_data)

    def _deactivate_unused_payment_methods(self, acquirer, payment_method_obj, wallee_methods):
        """Deactivate payment methods that are no longer available."""
        active_codes = [str(method.get('method_id', '')) for method in wallee_methods]
        inactive_methods = payment_method_obj.search([
            ('is_wallee', '=', True),
            ('code', 'not in', active_codes),
            ('provider_ids', 'in', acquirer.id)
        ])
        inactive_methods.write({
            'active': False,
            'provider_ids': [(3, acquirer.id)]
        })

    def _create_entity_query_filter(self, field_name, value, operator=CriteriaOperator.EQUALS):
        """Create an EntityQueryFilter with the given parameters.

        Args:
            field_name (str): Name of the field to filter on
            value: Value to filter by
            operator (CriteriaOperator): Operator to use for comparison, defaults to EQUALS

        Returns:
            EntityQueryFilter: Configured query filter
        """
        return EntityQueryFilter(
            field_name=field_name,
            operator=operator,
            type=EntityQueryFilterType.LEAF,
            value=value
        )

    def _update_existing_payment_method(self, method, new_name, new_image):
        """Update an existing payment method with new data."""
        update_vals = {'image': new_image}
        if method.name != new_name:
            update_vals['name'] = new_name
        if not method.active:
            update_vals['active'] = True
        method.write(update_vals)

    def _create_new_payment_method(self, acquirer, payment_method_obj, method_id, method_name, method_image):
        """Create a new payment method record."""
        return payment_method_obj.create({
            'name': method_name,
            'code': method_id,
            'is_wallee': True,
            'provider_ids': [(4, acquirer.id)],
            'image': method_image
        })

    def _read_image_file(self, image_path, output_format='PNG'):
        provider_log = self.env['payment.provider.log'].sudo()
        try:
            response = requests.get(image_path, timeout=10)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            error_message = str(e)
            _logger.error("Error fetching image: %s", error_message)

            # Log error
            provider_log._post_log({
                'name': str(response.status_code if 'response' in locals() else '500'),
                'description': 'Failed to fetch payment method image',
                'response_data': provider_log._format_response({
                    'error': error_message,
                    'image_path': image_path
                }),
                'provider_id': self.id,
                'source': 'ecommerce'
            })
            return False
        if response.status_code == 200:
            image_binary = BytesIO(response.content)
            svg_content = image_binary.getvalue().decode('utf-8')
            png_output = cairosvg.svg2png(bytestring=svg_content)
            image_binary = BytesIO(png_output)
            try:
                image = Image.open(image_binary)
            except Exception as e:
                raise ValueError(_("Error opening the image: %s",str(e)))
            if output_format.upper() not in ['PNG', 'JPEG']:
                raise ValueError(_("Invalid output format. Supported formats: PNG, JPEG."))
            if image.mode == 'RGBA':
                image = image.convert('RGB')
            output_buffer = BytesIO()
            image.save(output_buffer, format=output_format.upper())
            output_buffer.seek(0)
            image_base64 = base64.b64encode(output_buffer.read()).decode('utf-8')
            return image_base64
        _logger.error("Failed to fetch image: %s", response.status_code)
        return False

    def wallee_search_refund_id(self, refund_id):
        """Search for a refund by ID using Wallee SDK.

        Args:
            refund_id (int): The ID of the refund to search for

        Returns:
            Refund: The refund object if found, None otherwise
        """
        try:
            # Configure SDK with credentials
            configuration = Configuration(
                user_id=self.sudo().wallee_api_userid,
                api_secret=self.sudo().wallee_api_application_key
            )

            # Create refund service instance
            refund_service = RefundServiceApi(configuration)

            # Search for the refund
            refund = refund_service.read(self.sudo().wallee_api_spaceid, refund_id)
            return refund

        except Exception as e:
            _logger.error("Failed to search refund %s: %s", refund_id, str(e))
            return None
