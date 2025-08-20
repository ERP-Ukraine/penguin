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

import logging

from psycopg2 import OperationalError, Error
from werkzeug import urls

from odoo import api, models, fields, _
from odoo.addons.payment import utils as payment_utils
from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_repr
from ..controllers.main import WalleeController
from ..constants import (
    WALLEE_PENDING_STATES,
    WALLEE_REFUND_PENDING_STATES,
    WALLEE_TRANSACTION_STATES,
    WALLEE_INTERFACE_TYPES,
)

_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _name = 'payment.transaction'
    _inherit = ['payment.transaction', 'mail.thread']

    wallee_payment_method_id = fields.Integer(string='Wallee Payment Method ID', readonly=True)
    wallee_transaction_interface = fields.Selection(
        WALLEE_INTERFACE_TYPES,
        string='Wallee Interface',
        readonly=True
    )
    wallee_state = fields.Selection(
        WALLEE_TRANSACTION_STATES,
        string='Wallee Payment Status',
        readonly=True
    )
    wallee_transaction_id = fields.Integer(string='Wallee Transaction ID', readonly=True)
    is_wallee_refund = fields.Boolean(readonly=True)

    def _get_specific_rendering_values(self, processing_values):
        """Prepare Wallee-specific rendering values."""
        res = super()._get_specific_rendering_values(processing_values)
        if self.provider_code != 'wallee':
            return res

        self.ensure_one()

        try:
            # Initialize base values
            processing_values.update(self._prepare_base_wallee_values())
            processing_values.update(self._prepare_wallee_urls())

            # Get partner information
            partner_id, billing_address, shipping_address = self._get_wallee_address_info(self)

            # Prepare transaction details with exact reference
            tx_details = {
                'currency_name': self.currency_id.name,
                'name': self.reference,  # Use exact reference from model
                'partner_id': partner_id.id,
            }

            # Create or update Wallee transaction
            wallee_tx_values = self._prepare_wallee_tx_values(
                tx_details, partner_id, billing_address, shipping_address
            )

            # Create or update transaction with exact reference
            provider_reference = self._create_or_update_wallee_transaction(wallee_tx_values)
            if provider_reference:
                self._setup_wallee_payment_interface(processing_values, provider_reference)

            return processing_values

        except Exception as e:
            _logger.exception("Error processing Wallee payment: %s", str(e))
            raise ValidationError(_('Failed to process Wallee payment: %s', str(e)))

    def _set_transaction_date(self):
        self.write({
            'last_state_change': fields.Datetime.now(),
        })

    def _process_wallee_notification(self, notification_data):
        """Process the transaction based on Wallee notification data."""
        if self.provider_code != 'wallee':
            return

        if not self.provider_reference:
            raise ValidationError(_('Wallee: Missing provider reference'))

        try:
            self._cr.execute("SELECT 1 FROM payment_transaction WHERE id = %s FOR UPDATE NOWAIT", [self.id])
            return self._process_wallee_state(notification_data)

        except OperationalError as e:
            _logger.warning("Wallee: Unable to get transaction lock: %s", str(e))
            return False
        except Error as e:
            _logger.exception("Wallee: Database error: %s", str(e))
            return False
        except Exception as e:
            _logger.exception("Wallee: Error processing notification: %s", str(e))
            raise ValidationError(_("Failed to process Wallee transaction. Please try again.")) from e

    def _process_wallee_state(self, notification_data):
        """Process Wallee transaction state."""
        # Handle failed state early
        wallee_state = notification_data.get('wallee_state')
        if wallee_state == 'FAILED':
            return self._handle_failed_state(wallee_state)

        # Fetch and validate transaction
        try:
            wallee_trans = self._fetch_wallee_transaction_status()
        except ValidationError as e:
            _logger.error("Validation error fetching Wallee transaction: %s", str(e))
            raise ValidationError(_("Failed to validate Wallee transaction.")) from e
        except Exception as e:
            _logger.exception("Error fetching Wallee transaction: %s", str(e))
            raise ValidationError(_("Failed to fetch Wallee transaction status.")) from e

        if not self._verify_transaction_reference(wallee_trans):
            return False

        # Get state and process updates
        wallee_state = wallee_trans.state.value
        from_cron = notification_data.get('from_cron', False)

        # Handle cron updates
        if self._process_wallee_cron_state(wallee_state, from_cron):
            return True

        # Process final state
        return self._update_state_from_wallee(wallee_state)

    def _process_notification_data(self, notification_data):
        """Override of payment to process the transaction based on Wallee data."""
        super()._process_notification_data(notification_data)
        self.ensure_one()
        return self._process_wallee_notification(notification_data)

    def _handle_wallee_pending_update(self, data=None):
        """Handle pending transaction update for Wallee.
        
        :param dict data: Optional data for the update
        """
        # Implementation remains the same
        pass

    def wallee_refund_form_validate(self):
        response = self.provider_id.wallee_search_refund_id(self.provider_reference)
        if response is None:
            return False
        error = response.failure_reason
        wallee_state = response.state.value
        return_value = True
        self.write({'wallee_state': wallee_state})
        if wallee_state in WALLEE_REFUND_PENDING_STATES:
            self._set_transaction_date()
            return True
        if wallee_state == 'SUCCESSFUL':
            self._set_done()
            if not self.is_post_processed:
                self._post_process()
        elif wallee_state == 'PENDING':
            self._set_pending()
        else:
            self.write({
                'state_message': 'Wallee Refund FAILED: ' + error
            })
            _logger.info(error)
            self._set_canceled()
            return_value = False
        if self.provider_id.send_status_email:
            self.send_wallee_transaction_email()
        return return_value

    def get_partner_address(self, partner_id=None):
        """Get formatted partner address details with fallbacks to transaction fields."""
        partner = partner_id or self.partner_id
        if not partner:
            return {}

        partner_first_name, partner_last_name = payment_utils.split_partner_name(partner.name or '')

        # Get state and country codes
        partner_state = (partner.state_id and partner.state_id.name) or (self.partner_state_id and self.partner_state_id.name) or ""
        partner_country_code = (partner.country_id and partner.country_id.code) or (self.partner_country_id and self.partner_country_id.code) or ""

        # Build address data with fallbacks
        address_data = {
            "city": partner.city or self.partner_city or "",
            "emailAddress": partner.email or self.partner_email or "",
            "familyName": partner_last_name,
            "givenName": partner_first_name,
            "phoneNumber": partner.phone or self.partner_phone or "",
            "organizationName": self._get_organization_name(partner),
            "postcode": partner.zip or self.partner_zip or "",
            "street": partner.street or self.partner_address or "",
            "postalState": partner_state,
            "country": partner_country_code,
        }
        return address_data

    def _get_organization_name(self, partner):
        """Get organization name from partner details."""
        parent = partner.parent_id
        if not parent and not partner.company_name:
            return ""

        if parent:
            if not parent.company_name:
                return parent.name or ""
            if not parent.name or parent.company_name == parent.name:
                return parent.company_name
            return f"{parent.company_name} - {parent.name}"
            
        return partner.company_name

    def send_wallee_transaction_email(self):
        try:
            template_id = False
            if self.wallee_state in ['SUCCESSFUL', 'FULFILL']:
                template_id = self.env.ref('payment_wallee.wallee_email_template_payment_transaction_confirmed')
            elif self.wallee_state in ['FAILED', 'DECLINE', 'VOIDED']:
                template_id = self.env.ref('payment_wallee.wallee_email_template_payment_transaction_cancelled')
            if template_id:
                template_id.send_mail(self.id, force_send=True)
        except Exception as e:
            _logger.info(_("Error! Email cannot be send %s", str(e)))

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
                    "uniqueId": line.id,
                    "amountIncludingTax": float_repr(line.price_total, 2)
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
                    "uniqueId": line.id,
                    "amountIncludingTax": float_repr(line.price_total, 2)
                })
        if not line_details:
            line_details.append({
                'name': _("Total"),
                'quantity': 1,
                "type": "PRODUCT",
                "uniqueId": _("total"),
                "amountIncludingTax": float_repr(self.amount, 2)
            })
        return line_details

    def _send_status_email(self):
        """Send transaction status email if enabled in the provider configuration."""
        if self.provider_id.send_status_email:
            self.send_wallee_transaction_email()

    def _prepare_base_wallee_values(self):
        """Prepare the base Wallee transaction values."""
        values = {}
        if self.wallee_payment_method_id:
            values['wallee_payment_method'] = self.wallee_payment_method_id
        return values

    def _prepare_wallee_urls(self):
        """Prepare Wallee-specific URLs for the transaction."""
        base_url = self.provider_id.get_base_url()
        return {
            'successUrl': urls.url_join(base_url, WalleeController._success_url) + f"?txnId={self.id}",
            'failedUrl': urls.url_join(base_url, WalleeController._failed_url) + f"?txnId={self.id}",
            'wallee_redirect_url': urls.url_join(base_url, WalleeController._wallee_redirect_url)
        }

    def _setup_wallee_payment_interface(self, processing_values, provider_reference):
        """Set up the appropriate payment interface (redirect, iframe, or lightbox)."""
        try:
            # Get interface type from transaction or fallback to provider setting
            tx_interface = self.wallee_transaction_interface or self.provider_id.payment_page
            if tx_interface == 'iframe':
                # Get iframe JavaScript URL
                response = self.provider_id.wallee_build_javascript_url(provider_reference)
                if 'wallee_javascript_url' in response:
                    processing_values.update({
                        'wallee_tx_url': response['wallee_javascript_url'],
                        'wallee_tx_status': 'iframe'
                    })
            elif tx_interface == 'lightbox':
                # Get lightbox JavaScript URL
                response = self.provider_id.wallee_build_javascript_url(provider_reference)
                if 'wallee_lightbox_javascript_url' in response:
                    processing_values.update({
                        'wallee_tx_url': response['wallee_lightbox_javascript_url'],
                        'wallee_tx_status': 'lightbox',
                        'wallee_payment_method': {
                            'transaction_id': provider_reference,
                            'space_id': self.provider_id.wallee_api_spaceid,
                        }
                    })
            else:  # redirect
                # Get payment page URL
                response = self.provider_id.wallee_build_payment_page_url(provider_reference)
                if 'wallee_redirect_url' in response:
                    processing_values.update({
                        'wallee_tx_url': response['wallee_redirect_url'],
                        'wallee_tx_status': 'redirect'
                    })

            if not processing_values.get('wallee_tx_url'):
                error = response.get('error', _('Failed to get payment URL'))
                raise ValidationError(error)

            # Store the interface type
            self.write({'wallee_transaction_interface': tx_interface})

            # Log the processing values for debugging
            _logger.info("Wallee payment interface setup complete: %s", {
                'interface_type': tx_interface,
                'url': processing_values.get('wallee_tx_url'),
                'payment_method': processing_values.get('wallee_payment_method')
            })

        except Exception as e:
            _logger.exception("Error setting up Wallee payment interface: %s", str(e))
            raise ValidationError(_('Failed to set up payment interface: %s', str(e)))

    def _get_wallee_address_info(self, transaction):
        """Get billing and shipping address information."""
        # Determine partner for billing
        if transaction.sale_order_ids:
            partner_id = transaction.sale_order_ids[0].partner_invoice_id
        elif transaction.invoice_ids:
            partner_id = transaction.invoice_ids[0].partner_id
        else:
            partner_id = transaction.partner_id

        billing_address = self.get_partner_address(partner_id)

        # Determine partner for shipping
        if transaction.sale_order_ids and transaction.sale_order_ids[0].partner_shipping_id:
            partner_shipping_id = transaction.sale_order_ids[0].partner_shipping_id
        elif transaction.invoice_ids and transaction.invoice_ids[0].partner_shipping_id:
            partner_shipping_id = transaction.invoice_ids[0].partner_shipping_id
        else:
            partner_shipping_id = False

        shipping_address = self.get_partner_address(partner_shipping_id) if partner_shipping_id else billing_address.copy()

        return partner_id, billing_address, shipping_address

    def _prepare_wallee_tx_values(self, tx_details, partner_id, billing_address, shipping_address):
        """Prepare Wallee transaction values."""
        txline_details = self.get_wallee_line_details()

        return {
            'wallee_payment_method': self.wallee_payment_method_id,
            'txline_details': txline_details,
            'tx_details': tx_details,
            'partner_id': partner_id.id or self.partner_id.id,
            'billing_address': billing_address,
            'shipping_address': shipping_address
        }

    def _create_or_update_wallee_transaction(self, wallee_tx_values):
        """Create or update transaction on Wallee platform."""
        self.ensure_one()

        # Use select_for_update() to lock the record during transaction handling
        # NOWAIT ensures we don't hang if another process holds the lock.
        self.env.cr.execute('SELECT id FROM payment_transaction WHERE id = %s FOR UPDATE NOWAIT', (self.id,))

        # Get reference from payment transaction model
        payment_tx_ref = self.reference
        if not payment_tx_ref:
            raise ValidationError(_("Missing payment transaction reference"))

        # Search for existing transaction by exact reference match
        query_filter = self.provider_id._create_entity_query_filter(
            'merchantReference',
            payment_tx_ref.split('-')[0]
        )

        search_params = {
            'filter': query_filter,
            'orderBys': [
                {
                    'fieldName': 'id',
                    'sorting': 'DESC'
                }
            ]
        }
        response = self.provider_id.wallee_search_transaction_id(search_params)

        if response.get('status', 0) == 200 and response.get('data'):
            # Only consider transactions with exact reference match
            matching_transactions = list(response['data'])
            if matching_transactions:
                # Filter out invalid states
                valid_transactions = [tx for tx in matching_transactions if tx.state.value not in ['FAILED', 'DECLINE', 'VOIDED']]
                if valid_transactions:
                    # Use the most recent valid transaction
                    existing_tx = sorted(valid_transactions, key=lambda x: x.id, reverse=True)[0]
                    _logger.info("Found existing Wallee transaction %s with reference %s",
                               existing_tx.id, payment_tx_ref)
                    self.write({'provider_reference': str(existing_tx.id)})
                    self.provider_id.wallee_update_transaction(str(existing_tx.id), wallee_tx_values)
                    return str(existing_tx.id)
                else:
                    _logger.info("No valid transactions found for reference %s", payment_tx_ref)
            else:
                _logger.info("No transactions found with exact reference %s", payment_tx_ref)

        # Create new transaction only if we have the exact reference
        try:
            # Ensure tx_details has the exact reference from payment transaction
            tx_details = dict(wallee_tx_values.get('tx_details', {}))
            tx_details['name'] = payment_tx_ref
            wallee_tx_values['tx_details'] = tx_details

            _logger.info("Creating new Wallee transaction for reference %s", payment_tx_ref)
            response = self.provider_id.wallee_create_transaction(wallee_tx_values)
            provider_reference = response.get('trans_id')
            if not provider_reference:
                raise ValidationError(_("Failed to create Wallee transaction: No transaction ID returned"))

            self.write({'provider_reference': provider_reference})

        except Exception as e:
            _logger.exception("Error in Wallee transaction creation: %s", str(e))
            raise ValidationError(_("Failed to process Wallee transaction. Please try again."))

        return provider_reference

    def _update_wallee_transaction_state(self, provider_reference):
        """Update transaction state and handle previous transactions."""
        self.ensure_one()

        if provider_reference:
            # Cancel previous draft transactions with same reference
            prev_trans = self.env['payment.transaction'].sudo().search([
                ('id', 'not in', self.ids),
                ('provider_reference', '=', provider_reference),
                ('provider_id.code', '=', 'wallee'),
                ('wallee_state', 'not in', ['FULFILL', 'DECLINE', 'FAILED']),
                ('state', '=', 'draft')
            ])

            if prev_trans:
                prev_trans.write({'state': 'cancel'})

            # Update current transaction
            self.write({'provider_reference': provider_reference})

    @api.model
    def _get_tx_from_notification_data(self, provider, data):
        """ Override of payment to find the transaction based on Wallee data.

        :param str provider: The provider of the acquirer that handled the transaction
        :param dict data: The feedback data sent by the provider
        :return: The transaction if found
        :rtype: recordset of `payment.transaction`
        :raise: ValidationError if inconsistent data were received
        """
        transaction = super()._get_tx_from_notification_data(provider, data)
        if provider != 'wallee':
            return transaction

        txn_id = data.get('txnId')  # Get transaction ID from notification data
        if not txn_id:
            raise ValidationError(_('Wallee: Missing transaction ID in feedback data'))

        transaction = self.env['payment.transaction'].sudo().browse(int(txn_id))
        if not transaction.exists():
            raise ValidationError(_('Wallee: No transaction found for ID %s', txn_id))
        if len(transaction) > 1:
            raise ValidationError(_('Wallee: Multiple transactions found for ID %s', txn_id))

        # Validate that this is a Wallee transaction
        if transaction.provider_code != 'wallee':
            raise ValidationError(_('Wallee: Transaction %s is not a Wallee transaction', txn_id))

        return transaction

    def _create_payment(self, **extra_create_values):
        res = super()._create_payment()
        res.update({
            'is_wallee_refund': self.is_wallee_refund
        })
        return res

    def _process_wallee_transaction(self):
        """Handle Wallee transaction processing and state management."""
        self.ensure_one()

        # Update transaction name to match Odoo reference
        if self.provider_reference and self.reference:
            self.provider_id.wallee_update_transaction_name(
                self.provider_reference,
            )

        # Process transaction state
        result = super()._process_wallee_transaction()

        # Update transaction state in model
        if result and self.wallee_state:
            self.write({
                'state': 'done' if self.wallee_state == 'FULFILL' else 'pending'
            })

        return result

    def _get_wallee_transaction_details(self):
        """Fetches transaction details from Wallee API and validates them."""
        self.ensure_one()

        query_filter = self.provider_id._create_entity_query_filter(
            'id',
            self.provider_reference
        )
        search_params = {
            'filter': query_filter,
            'orderBys': [{'fieldName': 'id', 'sorting': 'DESC'}]
        }

        response = self.provider_id.wallee_search_transaction_id(search_params)
        if response.get('status') != 200:
            _logger.error(
                "Failed response from Wallee API for transaction with reference %s",
                self.reference
            )
            raise ValidationError(_('Wallee: Failed to fetch transaction status.')) 

        res_data = response.get('data', [])
        if not res_data:
            _logger.warning(
                "No transaction found via Wallee API for reference %s",
                self.reference
            )
            return None

        wallee_trans = res_data[0]

        # Verify reference match - Crucial check
        if wallee_trans.merchant_reference != self.reference:
            _logger.error(
                "Reference mismatch in Wallee transaction with reference %s",
                self.reference
            )
            raise ValidationError(_("Wallee: Transaction reference mismatch"))

        return wallee_trans

    def _handle_cron_pending_update(self, wallee_state, from_cron):
        """Handles updates for pending transactions initiated by cron.
           Returns True if update is handled here, False otherwise.
        """
        self.ensure_one()
        if not from_cron:
            return False # Only applies to cron updates

        # Check if the transaction is effectively still pending or unchanged from Wallee's side
        is_still_pending_or_unchanged = (
            # Case 1: Odoo has no Wallee state yet, Wallee is pending
            (not self.wallee_state and wallee_state in WALLEE_PENDING_STATES) or
            # Case 2: Odoo state is pending, Wallee state is also (still) pending
            (self.wallee_state in WALLEE_PENDING_STATES and wallee_state in WALLEE_PENDING_STATES) or
            # Case 3: Wallee state reported by API is the same as the stored one
            (self.wallee_state == wallee_state)
        )

        if is_still_pending_or_unchanged:
            # For cron updates where the state is still pending/unchanged,
            # just update the wallee_state field (if needed) and don't change Odoo state.
            if self.wallee_state != wallee_state:
                _logger.info(
                    "Cron update for tx %s: Odoo state %s, Wallee state %s -> %s. Updating wallee_state field only.",
                    self.reference, self.state, self.wallee_state, wallee_state
                )
                self.write({'wallee_state': wallee_state})
            else:
                 _logger.info(
                    "Cron update for tx %s: Wallee state %s is unchanged. No action needed.",
                    self.reference, wallee_state
                )
            return True # Indicate that processing is handled (no further state change needed now)

        return False # Indicate normal processing should continue

    def _update_state_from_wallee(self, wallee_state):
        """Updates the Odoo transaction state based on the Wallee state."""
        self.ensure_one()
        _logger.info(
            "Processing state update for transaction with reference %s",
            self.reference
        )

        # Always update the local Wallee state field if it differs
        if self.wallee_state != wallee_state:
            self.write({'wallee_state': wallee_state})

        # Process state changes based on the NEW Wallee state
        if wallee_state in WALLEE_PENDING_STATES:
            if self.state != 'pending':
                self._set_pending()
                self._set_transaction_date()
            return

        if wallee_state == 'FULFILL':
            # Check if already done to avoid redundant post-processing/emails
            if self.state != 'done':
                self._set_done()
                # Post-processing should happen only once when moving to 'done'
                if not self.is_post_processed:
                    self._post_process()
                self._send_status_email() # Send confirmation email
            return

        if wallee_state in ['FAILED', 'DECLINE']:
            # Check if already canceled
            if self.state != 'cancel':
                self._set_canceled()
                self._send_status_email() # Send failure email
            return

        # Handle other terminal states like AUTHORIZED, COMPLETED, VOIDED if needed
        # For now, log unhandled states that are not pending/fulfill/failed/decline
        if wallee_state not in ['AUTHORIZED', 'COMPLETED', 'VOIDED']: # Add known but unhandled states here
            _logger.warning(
                "Unhandled payment state encountered for transaction with reference %s",
                self.reference
            )

    def _set_transaction_date(self):
        """ Sets the transaction date only if not already set. """
        for tx in self.filtered(lambda t: not t.transaction_date):
             tx.transaction_date = fields.Datetime.now()


    # CRON JOB
    def _cron_check_wallee_pending_transactions(self):
        """ Cron job to check the status of pending Wallee transactions. """
        _logger.info("Starting Wallee pending transactions check cron job...")
        # Search criteria:
        # - Provider is 'wallee'
        # - Odoo state is 'pending' (meaning not yet terminal)
        # - Optional: Filter by wallee_state being in pending states if we only want to check those explicitly marked pending by Wallee
        #   However, checking all 'pending' Odoo states is safer as some might not have received a Wallee state yet.
        # - Optional: Add a time filter (e.g., created_date > now - 7 days) to avoid checking very old transactions.
        pending_transactions = self.search([
            ('provider_code', '=', 'wallee'),
            ('state', '=', 'pending'),
            # ('wallee_state', 'in', WALLEE_PENDING_STATES) # Consider if this filter is too restrictive
        ])

        if not pending_transactions:
            _logger.info("No pending Wallee transactions found matching criteria.")
            return

        _logger.info("Found %d pending Wallee transactions to check.", len(pending_transactions))
        processed_count = 0
        failed_count = 0

        for tx in pending_transactions:
            try:
                # Use the standard notification processing logic
                success = tx._process_notification_data({'from_cron': True})

                if success:
                    processed_count += 1
                else:
                    failed_count += 1
                    _logger.warning(
                        "Temporary error processing transaction with reference %s",
                        tx.reference
                    )

                self.env.cr.commit()

            except ValidationError:
                failed_count += 1
                _logger.error(
                    "Validation error processing transaction with reference %s",
                    tx.reference,
                    exc_info=True
                )
                self.env.cr.rollback()

            except Exception:
                failed_count += 1
                _logger.error(
                    "Unexpected error processing transaction with reference %s",
                    tx.reference,
                    exc_info=True
                )
                self.env.cr.rollback()

        _logger.info(
            "Completed pending transactions check. Processed: %d, Failed: %d",
            processed_count, failed_count
        )

    def _process_notification_data(self, notification_data):
        """ Override of payment to process the transaction based on Wallee data.

        Note: self.ensure_one()

        :param dict notification_data: The feedback data potentially from webhook or cron
        :return: bool: True if the processing was successful or handled, False otherwise
        :raise: ValidationError if inconsistent data were received or critical processing failed
        """
        # Call super first, it might handle generic processing or initial checks
        super()._process_notification_data(notification_data)
        self.ensure_one()

        if self.provider_code != 'wallee':
            _logger.debug("Skipping Wallee processing for tx %s, provider is %s", self.reference, self.provider_code)
            return True # Not a Wallee transaction, processing considered successful

        if not self.provider_reference:
            # This should ideally not happen if _get_tx_from_notification_data worked correctly
            _logger.error('Wallee: Missing provider reference (Wallee Tx ID) for Odoo transaction %s (ID %s)',
                          self.reference, self.id)
            # Returning False indicates a processing issue for this specific transaction.
            return False

        _logger.info("Processing Wallee notification for tx %s (Provider Ref: %s)", self.reference, self.provider_reference)
        from_cron = notification_data.get('from_cron', False)

        try:
            # Attempt to acquire a row-level lock to prevent race conditions during state updates
            # NOWAIT ensures we don't hang if another process holds the lock.
            self._cr.execute("SELECT 1 FROM payment_transaction WHERE id = %s FOR UPDATE NOWAIT", [self.id])

            # --- Fast path for explicit FAILED state from notification data ---
            # This can come directly from webhook if Wallee sends a final FAILED event
            wallee_state_notif = notification_data.get('wallee_state') # Check if notification data provides state
            if wallee_state_notif == 'FAILED':
                _logger.info("Notification data indicates transaction %s state is FAILED. Processing immediately.", self.reference)
                # Use the dedicated state update method, ensuring Odoo state becomes 'cancel'
                self._update_state_from_wallee('FAILED')
                return True # Processing handled successfully

            # --- Fetch current details from Wallee---
            # This is necessary to get the definitive current state from the source of truth.
            wallee_trans = self._get_wallee_transaction_details()

            # Handle case where API call couldn't find the transaction (logged in helper)
            if wallee_trans is None:
                 _logger.warning("Wallee API did not find transaction %s (Provider Ref: %s). Skipping state update.",
                                 self.reference, self.provider_reference)
                 # Don't change state if API can't confirm. Might be temporary issue or already processed/deleted in Wallee.
                 # Returning True as we handled the notification, even if no state change occurred.
                 return True

            wallee_state_api = wallee_trans.state.value
            _logger.info("Wallee API reported state '%s' for tx %s", wallee_state_api, self.reference)

            # --- Handle specific cron/pending scenarios ---
            # Check if this is a cron job update for a transaction that's still pending/unchanged.
            if self._handle_cron_pending_update(wallee_state_api, from_cron):
                # The helper logged and potentially updated wallee_state field. No further action needed here.
                return True # Update handled successfully by the helper.

            # --- Process final state transition based on API result ---
            # If not handled by the cron/pending logic, update Odoo state based on the API state.
            self._update_state_from_wallee(wallee_state_api)
            return True # State update processed successfully.

        except OperationalError:
            # Could not acquire lock (FOR UPDATE NOWAIT failed).
            # This means another process (e.g., another webhook instance, cron job) is likely already processing this transaction.
            # Log this situation and return False to signal that processing should be potentially retried later.
            _logger.warning(
                "Wallee: Unable to acquire lock for transaction %s (ID: %s). Notification processing deferred as it might be handled by another process.",
                self.reference, self.id
            )
            return False
        except Error as e:
            # Database-level error during lock acquisition or state write.
            _logger.exception(
                "Wallee: Database error during notification processing for tx %s (ID: %s): %s",
                 self.reference, self.id, e
            )
            self.env.cr.rollback() # Rollback any partial changes in this specific attempt
            # Return False to signal processing failure without raising to the caller (e.g., webhook controller),
            # allowing the system (e.g., cron) to potentially retry later.
            return False
        except ValidationError as e:
            # Specific validation error raised by helpers (e.g., API fetch failed critically, reference mismatch).
            _logger.error(
                "Wallee: Validation error processing notification for tx %s (ID: %s): %s",
                 self.reference, self.id, e
            )
            self.env.cr.rollback() # Rollback potential changes
            # Re-raising ValidationError makes the problem explicit in logs and potentially alerts monitoring.
            # If this causes issues with the webhook controller (e.g., it expects True/False),
            # consider changing this to `return False`. For now, re-raise is preferred for clarity.
            raise # Re-raise the caught ValidationError
        except Exception as e:
            # Catch-all for any other unexpected errors during processing.
            _logger.exception(
                "Wallee: Unexpected error processing notification for tx %s (ID: %s): %s",
                 self.reference, self.id, e
            )
            self.env.cr.rollback() # Rollback potential changes
            # Raise a generic ValidationError to the caller to indicate a processing failure.
            # Include the original exception for context.
            raise ValidationError(_(
                "Wallee: An unexpected error occurred while processing the transaction notification for %s.", self.reference
            )) from e

    def _verify_transaction_reference(self, wallee_trans):
        """Verify that transaction reference matches."""
        if wallee_trans.merchant_reference != self.reference:
            _logger.error(
                "Reference mismatch for tx %(tx_ref)s: Wallee reference %(wallee_ref)s, expected %(expected_ref)s",
                {
                    'tx_ref': self.provider_reference,
                    'wallee_ref': wallee_trans.merchant_reference,
                    'expected_ref': self.reference
                }
            )
            return False
        return True

    def _update_state_from_wallee(self, wallee_state):
        """Update transaction state based on Wallee state."""
        self.write({'wallee_state': wallee_state})

        if wallee_state in WALLEE_PENDING_STATES and self.state != 'pending':
            self._set_pending()
            self._set_transaction_date()
            return True

        if wallee_state == 'FULFILL':
            self._set_done()
            if not self.is_post_processed:
                self._post_process()
            self._send_status_email()
            return True

        if wallee_state in ['FAILED', 'DECLINE']:
            self._set_canceled()
            self._send_status_email()
            return True

        return False
