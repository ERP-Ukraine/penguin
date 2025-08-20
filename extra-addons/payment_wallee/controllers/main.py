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
from datetime import timedelta

from odoo import fields, http, _
from odoo.addons.account_payment.controllers.payment import PaymentPortal
from odoo.addons.payment.controllers.post_processing import PaymentPostProcessing
from odoo.exceptions import AccessError, MissingError, ValidationError
from odoo.http import request, route
from ..constants import WALLEE_PENDING_STATES

_logger = logging.getLogger(__name__)


class WalleePaymentPortal(PaymentPortal):

    @route('/invoice/transaction/<int:invoice_id>', type='json', auth='public')
    def invoice_transaction(self, invoice_id, access_token, **kwargs):
        """ Create a draft transaction and return its processing values.

        :param int invoice_id: The invoice to pay, as an `account.move` id
        :param str access_token: The access token used to authenticate the request
        :param dict kwargs: Locally unused data passed to `_create_transaction`
        :return: The mandatory values for the processing of the transaction
        :rtype: dict
        :raise: ValidationError if the invoice id or the access token is invalid
        """
        # Check the invoice id and the access token
        try:
            invoice_sudo = self._document_check_access('account.move', invoice_id, access_token)
            if invoice_sudo and invoice_sudo.amount_residual:
                kwargs.update({
                    'amount': invoice_sudo.amount_residual
                })
        except MissingError as error:
            raise error
        except AccessError:
            raise ValidationError(_("The access token is invalid."))
        return super().invoice_transaction(invoice_id, access_token, **kwargs)

    @http.route(['/payment/wallee/payment_method/update'], type='json', auth='public')
    def wallee_update_payment_method(self, **kwargs):
        """Update payment method information in the transaction record."""
        try:
            method_id = kwargs.get('method_id')
            space_id = kwargs.get('space_id')
            trans_interface = kwargs.get('trans_interface')
            one_click_mode = kwargs.get('one_click_mode')
            transaction_id = kwargs.get('trans_id')

            if None in [method_id, space_id, trans_interface, one_click_mode]:
                raise ValidationError(_('Missing required payment method information.'))

            if transaction_id:
                transaction = request.env['payment.transaction'].sudo().search([('provider_reference','=',transaction_id)])
                if transaction.exists():
                    # Update transaction with Wallee-specific data
                    transaction.write({
                        'wallee_payment_method_id': method_id,
                        'wallee_transaction_interface': 'redirect' if trans_interface == 'DataCollectionType.OFFSITE' else 'iframe',
                    })

            return {'success': True}

        except Exception as e:
            _logger.exception("Error updating Wallee payment method: %s", str(e))
            return {
                'success': False,
                'error': str(e),
            }

class WalleePostPaymentController(PaymentPostProcessing):

    @http.route()
    def poll_status(self, **_kwargs):
        """Poll the status of pending transactions."""
        res = super().poll_status(**_kwargs)
        limit_date = fields.Datetime.now() - timedelta(days=1)
        monitored_txn = self._get_monitored_transaction()

        if (monitored_txn and
            monitored_txn.last_state_change >= limit_date and
            monitored_txn.provider_code == 'wallee' and
            monitored_txn.wallee_state in WALLEE_PENDING_STATES):
            monitored_txn._process_notification_data({})

        return res

class WalleeController(http.Controller):
    _success_url = '/payment/wallee/success'
    _failed_url = '/payment/wallee/failed'
    _wallee_redirect_url = '/payment/wallee/redirect'

    @http.route(['/payment/wallee/redirect'], type='http', auth='public', website=True)
    def wallee_form_redirect(self, **post):
        """Handle redirection after payment."""
        # Check if we have a transaction ID
        tx_id = post.get('txnId')
        if tx_id:
            try:
                tx = request.env['payment.transaction'].sudo().browse(int(tx_id))
                if tx and tx.provider_code == 'wallee' and tx.state not in ['done', 'cancel', 'error']:
                    # Transaction exists and is not in final state
                    # Let the model handle the notification data
                    notification_data = {**post, 'provider_code': 'wallee', 'txnId': tx_id}
                    tx._handle_notification_data('wallee', notification_data)
            except Exception as e:
                _logger.exception("Wallee: error processing redirect: %s", str(e))

        # Redirect to payment status page
        return request.redirect('/payment/status')

    @http.route(['/payment/wallee/success', '/payment/wallee/failed'], type='http', auth='public', csrf=False, website=True)
    def wallee_form_feedback(self, **post):
        """Handle the feedback from Wallee."""
        # Get transaction ID from post data or query parameters
        tx_id = post.get('txnId') or request.params.get('txnId')

        if not tx_id:
            _logger.warning("Wallee: received feedback without transaction ID")
            return request.redirect('/payment/status')

        try:
            tx = request.env['payment.transaction'].sudo().browse(int(tx_id))
            if not tx:
                _logger.warning("Wallee: received feedback for non-existing transaction ID: %s", tx_id)
                return request.redirect('/payment/status')

            # Verify transaction provider
            if tx.provider_code != 'wallee':
                _logger.warning("Wallee: received feedback for non-Wallee transaction: %s", tx_id)
                return request.redirect('/payment/status')

            # Determine transaction state based on the endpoint and current state
            notification_data = {**post, 'provider_code': 'wallee', 'txnId': tx_id}

            if request.httprequest.path == self._failed_url:
                notification_data['wallee_state'] = 'FAILED'
            elif request.httprequest.path == self._success_url:
                # Check if transaction is already completed
                if tx.state == 'done':
                    _logger.info("Wallee: transaction %s is already completed", tx_id)
                    return request.redirect('/payment/status')
                notification_data['wallee_state'] = 'FULFILL'

            # Let the model handle the notification data
            tx._handle_notification_data('wallee', notification_data)

        except Exception as e:
            _logger.exception("Wallee: error processing payment feedback: %s", str(e))

        return request.redirect('/payment/status')

    @http.route(['/payment/wallee/unexpected'], type='http', auth='public', csrf=False, website=True)
    def wallee_unexpected_form_feedback(self, **post):
        """Handle unexpected payment outcomes."""
        _logger.warning("Wallee: received unexpected payment feedback: %s", post)
        return request.redirect('/payment/status')
