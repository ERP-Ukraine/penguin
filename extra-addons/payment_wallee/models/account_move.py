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
import json
import logging

from wallee import Configuration
from wallee.api import TransactionServiceApi, RefundServiceApi
from wallee.rest import ApiException as WalleeApiException

from odoo import api, models, fields, _
from odoo.exceptions import UserError, ValidationError
from ..constants import WALLEE_REFUND_TYPES

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = 'account.move'

    # Field Definitions
    filter_refund = fields.Selection(
        WALLEE_REFUND_TYPES,
        default='MERCHANT_INITIATED_ONLINE',
        string='Refund Type',
        required=True,
        help='Refund base on this type. You can not Modify and Cancel if the invoice is already reconciled'
    )
    is_wallee_refund = fields.Boolean(
        compute='_compute_is_wallee_refund',
        store=True,
        default=False
    )
    is_wallee_active = fields.Boolean()

    def assign_outstanding_credit(self, credit_aml_id):
        if self.is_wallee_refund and self.env.context.get('is_wallee_refund'):
            return True
        return super().assign_outstanding_credit(credit_aml_id)

    @api.depends('reversed_entry_id', 'reversed_entry_id.transaction_ids.state', 'reversed_entry_id.transaction_ids.provider_id')
    def _compute_is_wallee_refund(self):
        """Compute whether the move is a Wallee refund
        """
        # Get all Wallee provider IDs once
        wallee_providers = self.env['payment.provider'].search([('code', '=', 'wallee')]).ids
        # Get all done transactions for the reversed entry
        for record in self:
            done_transactions = record.reversed_entry_id.transaction_ids.filtered(
                lambda t: t.provider_id.id in wallee_providers and t.state == 'done'
            )
            record.is_wallee_refund = bool(done_transactions)

    def _get_refund_context(self):
        """Gets the Wallee acquirer and original transaction for the refund.
           Performs initial validations.
        """
        self.ensure_one()
        if not self.reversed_entry_id:
            raise UserError(_("This refund is not linked to an original invoice."))

        original_invoice = self.reversed_entry_id
        wallee_transactions = original_invoice.transaction_ids.filtered(lambda r: r.provider_code == 'wallee')

        if not wallee_transactions:
            raise UserError(_("The original invoice is not linked to a Wallee transaction."))

        # Assuming one Wallee transaction per invoice for simplicity, take the latest one.
        # Sort by ID desc and limit to 1 to get the most recent transaction reliably
        original_tx = wallee_transactions.sorted(key=lambda tx: tx.id, reverse=True)[:1]
        if not original_tx:
            raise UserError(_("Could not find the latest Wallee transaction for the original invoice."))

        wallee_acquirer = original_tx.provider_id
        if not wallee_acquirer:
            raise UserError(_("Could not determine the Wallee payment provider from the original transaction."))

        if self.currency_id != original_invoice.currency_id:
            raise ValidationError(_("Refund currency must match the original invoice currency (%(currency)s)."),
                                 {'currency': original_invoice.currency_id.name})

        return wallee_acquirer, original_tx

    def _create_refund_payment_transaction(self, acquirer, original_tx):
        """Creates the Odoo payment.transaction record for the refund."""
        self.ensure_one()
        refund_transaction_vals = {
            'amount': -1 * self.amount_total, # Refund amount is negative
            'currency_id': self.currency_id.id,
            'partner_id': self.partner_id.id,
            'provider_id': acquirer.id,
            'invoice_ids': [(6, 0, self.ids)],
            'operation': 'refund',
            'payment_method_id': original_tx.payment_method_id.id,
            # Link refund tx to the original tx for traceability
            'source_transaction_id': original_tx.id,
            'is_wallee_refund': True, # Custom flag if needed
        }
        refund_transaction = self.env['payment.transaction'].sudo().create(refund_transaction_vals)
        # Use Odoo's sequence for reference, Wallee uses external_id and its own ID
        # refund_transaction.reference might be generated automatically
        _logger.info("Created refund transaction %(ref)s for Wallee refund of invoice %(invoice)s.",
                     {'ref': refund_transaction.reference, 'invoice': self.name})
        return refund_transaction

    def _fetch_wallee_transaction_data(self, original_tx):
        """Fetch original transaction data from Wallee API."""
        self.ensure_one()
        acquirer = original_tx.provider_id.sudo()
        space_id = acquirer.wallee_api_spaceid
        provider_log = self.env['payment.provider.log'].sudo()

        try:
            configuration = Configuration(
                user_id=acquirer.wallee_api_userid,
                api_secret=acquirer.wallee_api_application_key
            )
            transaction_service = TransactionServiceApi(configuration)
            response = transaction_service.read(space_id, int(original_tx.provider_reference))

            # Log successful fetch
            provider_log._post_log({
                'name': '200',
                'description': f'Fetch Transaction Data - {original_tx.reference}',
                'response_data': provider_log._format_response({
                    'transaction_id': original_tx.provider_reference,
                    'space_id': space_id
                }),
                'provider_id': acquirer.id,
                'source': 'ecommerce'
            })

            return response

        except WalleeApiException as e:
            error_msg = e.body if hasattr(e, 'body') and e.body else str(e)
            _logger.error("Wallee API error fetching original transaction %(ref)s: %(error)s", {
                'ref': original_tx.provider_reference,
                'error': error_msg
            })

            # Log error
            provider_log._post_log({
                'name': '500',
                'description': f'Failed to Fetch Transaction Data - {original_tx.reference}',
                'response_data': provider_log._format_response({
                    'error': error_msg,
                    'transaction_id': original_tx.provider_reference,
                    'space_id': space_id
                }),
                'provider_id': acquirer.id,
                'source': 'ecommerce'
            })

            raise UserError(_("Could not fetch original transaction details from Wallee (ID: %(tx_id)s). Error: %(error)s"),
                          {'tx_id': original_tx.provider_reference, 'error': error_msg})
        except ValueError as e:
            error_msg = f"Invalid transaction reference format: {str(e)}"
            _logger.error(error_msg)

            # Log error for invalid reference
            provider_log._post_log({
                'name': '400',
                'description': f'Invalid Transaction Reference - {original_tx.reference}',
                'response_data': provider_log._format_response({
                    'error': error_msg,
                    'transaction_id': original_tx.provider_reference,
                    'space_id': space_id
                }),
                'provider_id': acquirer.id,
                'source': 'ecommerce'
            })

            raise UserError(error_msg)

    def _validate_wallee_line_match(self, wallee_item, refund_line):
        """Validate amount match between Wallee item and refund line."""
        if not fields.Float.is_zero(
            wallee_item.amount_including_tax - abs(refund_line.price_total),
            precision_rounding=self.currency_id.rounding
        ):
            error_msg = _(
                "Refund amount mismatch for item '%(name)s'. Original Wallee amount (incl. tax): %(orig)s, "
                "Refund line amount (total): %(refund)s",
                {
                    'name': refund_line.name or '',
                    'orig': wallee_item.amount_including_tax,
                    'refund': abs(refund_line.price_total)
                }
            )
            _logger.error(error_msg)
            raise UserError(error_msg)
        return True

    def _find_matching_wallee_item(self, refund_line, original_line_items, ids_to_process):
        """Find matching Wallee item for a refund line."""
        matched_items = [
            item for item in original_line_items
            if item.unique_id and item.unique_id.isdigit()
            and int(item.unique_id) in ids_to_process
        ]

        if not matched_items:
            return None

        for item_id in list(ids_to_process):
            specific_item = next(
                (item for item in matched_items
                 if item.unique_id and item.unique_id.isdigit()
                 and int(item.unique_id) == item_id),
                None
            )
            if specific_item and self._validate_wallee_line_match(specific_item, refund_line):
                ids_to_process.remove(item_id)
                return specific_item
        return None

    def _get_refundable_lines(self, source_lines):
        """Get refundable product lines with non-zero price."""
        return source_lines.filtered(
            lambda l: l.display_type == 'product' and l.price_total != 0
        )

    def _create_reduction_entry(self, matched_item, refund_line):
        """Create a reduction entry for the matched item."""
        return {
            "lineItemUniqueId": matched_item.unique_id,
            "quantityReduction": float(refund_line.quantity),
            "unitPriceReduction": 0.0
        }

    def _match_refund_line(self, refund_line, original_line_items, invoice_line_ids, sale_line_ids):
        """Match a refund line with original transaction items."""
        # Try matching with invoice lines first
        matched_item = self._find_matching_wallee_item(
            refund_line, original_line_items, invoice_line_ids
        )

        # If no match, try with sale order lines
        if not matched_item and sale_line_ids:
            _logger.info(
                "No match found using invoice lines for '%(name)s'. Trying sale order lines.",
                {'name': refund_line.name or ''}
            )
            matched_item = self._find_matching_wallee_item(
                refund_line, original_line_items, sale_line_ids
            )

        if not matched_item:
            raise UserError(
                _("Could not match refund line '%(name)s' (Product: %(product)s) to any corresponding item "
                  "in the original Wallee transaction using available IDs."),
                {'name': refund_line.name or '',
                 'product': refund_line.product_id.display_name or ''}
            )

        return matched_item

    def _validate_refund_prerequisites(self, original_tx, original_line_items):
        """Validate prerequisites for refund preparation."""
        if not original_line_items:
            _logger.warning("Original Wallee transaction %(ref)s has no line items. Cannot perform line-item based refund.",
                          {'ref': original_tx.provider_reference})
            return False

        original_invoice = self.reversed_entry_id
        if not original_invoice:
            raise UserError(_("Cannot prepare reductions: Original invoice link is missing."))

        return original_invoice

    def _prepare_wallee_refund_reductions(self, original_tx):
        """Prepares the line item reductions for the Wallee API call.
           Validates refund lines against original transaction lines.
        """
        self.ensure_one()

        # Fetch original transaction data
        original_wallee_tx_data = self._fetch_wallee_transaction_data(original_tx)
        original_line_items = original_wallee_tx_data.line_items or []

        # Validate prerequisites
        original_invoice = self._validate_refund_prerequisites(original_tx, original_line_items)
        if not original_invoice:
            return []

        # Get refundable lines
        refund_lines = self._get_refundable_lines(self.invoice_line_ids)
        invoice_line_ids = list(self._get_refundable_lines(original_invoice.invoice_line_ids).ids)
        sale_line_ids = list(self._get_refundable_lines(self.line_ids).sale_line_ids.ids)

        # Process refund lines
        reductions = []
        for refund_line in refund_lines:
            matched_item = self._match_refund_line(refund_line, original_line_items, invoice_line_ids, sale_line_ids)
            reductions.append(self._create_reduction_entry(matched_item, refund_line))

        if not reductions and refund_lines:
            raise UserError(_("Failed to generate any refund line item reductions. "
                            "Please verify refund lines and their link to the original transaction."))

        return reductions

    def _get_wallee_state_value(self, refund_data):
        """Safely extract state value from refund data."""
        if not hasattr(refund_data, 'state'):
            return 'UNKNOWN'

        if hasattr(refund_data.state, 'value'):
            return refund_data.state.value

        return str(refund_data.state)

    def _execute_wallee_refund(self, acquirer, original_tx, refund_tx, reductions):
        """Execute the refund API call to Wallee."""
        space_id = acquirer.wallee_api_spaceid
        configuration = Configuration(
            user_id=acquirer.wallee_api_userid,
            api_secret=acquirer.wallee_api_application_key
        )
        refund_service = RefundServiceApi(configuration)

        refund_create = {
            "externalId": refund_tx.reference,
            "merchantReference": str(refund_tx.reference),  # Add merchant reference back
            "reductions": reductions,
            "transaction": int(original_tx.provider_reference),
            "type": "MERCHANT_INITIATED_ONLINE"
        }

        _logger.info("Attempting Wallee refund for Odoo Tx %(ref)s. Payload: %(payload)s", {
            'ref': refund_tx.reference,
            'payload': refund_create
        })

        try:
            refund_data = refund_service.refund(space_id, refund_create)
            state_value = self._get_wallee_state_value(refund_data)
            _logger.info("Wallee refund API call successful for Odoo Tx %(ref)s. Wallee Refund ID: %(id)s, State: %(state)s",
                        {'ref': refund_tx.reference, 'id': refund_data.id, 'state': state_value})
            refund_tx.write({
                'provider_reference': refund_data.id
            })
            return refund_data, None  # Return data, no error
        except WalleeApiException as e:
            error_msg = e.body if hasattr(e, 'body') and e.body else str(e)
            _logger.error("Wallee API error during refund: %(error)s", {'error': error_msg})
            return None, error_msg
        except (ValueError, AttributeError) as e:
            error_msg = f"Error processing refund: {str(e)}"
            _logger.error(error_msg)
            return None, error_msg

    def _process_wallee_refund_result(self, refund_tx, refund_data, error_message=None):
        """Process the result of a Wallee refund API call."""
        if error_message:
            error_message = str(error_message)
            error_message_dict = json.loads(error_message)
            if isinstance(error_message_dict, dict) and 'message' in error_message_dict:
                error_message = error_message_dict['message']
            _logger.error("Wallee refund error: %(error)s", {'error': error_message})
            refund_tx.write({
                'state': 'error',
                'state_message': error_message,
            })
            return self._show_wallee_error_popup(error_message)  # Show error popup

        if not refund_data or not hasattr(refund_data, 'id'):
            error_message = _("Invalid response from Wallee refund API")
            _logger.error(error_message)
            refund_tx.write({
                'state': 'error',
                'state_message': error_message,
            })
            return self._show_wallee_error_popup(error_message)  # Show error popup

        try:
            state_value = self._get_wallee_state_value(refund_data)
            _logger.info(
                "Processing Wallee refund result for Tx %(ref)s (Wallee ID: %(id)s, State: %(state)s)",
                {
                    'ref': refund_tx.reference,
                    'id': refund_data.id,
                    'state': state_value
                }
            )
            refund_tx.wallee_refund_form_validate()
            return True
        except (AttributeError, ValueError) as e:
            error_message = _("Error processing Wallee refund result: %(error)s", {'error': str(e)})
            _logger.exception(error_message)
            refund_tx.write({
                'state': 'error',
                'state_message': error_message,
            })
            return self._show_wallee_error_popup(error_message)  # Show error popup

    def _show_wallee_error_popup(self, error_message):
        """Returns action dictionary to show a warning popup."""
        _logger.info("Showing Wallee error popup: %(error)s", {'error': error_message})
        return {
            'name': _('Wallee Refund Error'),
            'type': 'ir.actions.act_window',
            'res_model': 'warning.message.wizard', # Assuming this custom wizard exists
            'view_id': self.env.ref('payment_wallee.view_warning_message_wizard').id,
            'view_mode': 'form',
            'context': {'default_message': error_message},
            'target': 'new'
        }

    def action_wallee_refund(self):
        """Orchestrates the Wallee refund process."""
        self.ensure_one()
        _logger.info("Starting Wallee refund action for invoice %(invoice)s", {'invoice': self.name})

        try:
            # 1. Get context and perform initial checks
            acquirer, original_tx = self._get_refund_context()
            _logger.info("Refund context acquired for invoice %(invoice)s. Acquirer: %(acquirer)s, Original Tx: %(original_tx)s",
                         {'invoice': self.name, 'acquirer': acquirer.name, 'original_tx': original_tx.reference})

            # 2. Create the Odoo refund transaction
            refund_tx = self._create_refund_payment_transaction(acquirer, original_tx)

            # 3. Prepare line item reductions (if applicable)
            reductions = self._prepare_wallee_refund_reductions(original_tx)
            _logger.info("Prepared %(count)d refund reductions for Tx %(ref)s.", {
                'count': len(reductions),
                'ref': refund_tx.reference
            })

            # 4. Execute the refund call
            refund_data, error_message = self._execute_wallee_refund(acquirer, original_tx, refund_tx, reductions)

            # 5. Process the result
            return self._process_wallee_refund_result(refund_tx, refund_data, error_message)

        except (UserError, ValidationError, WalleeApiException) as e:
            # Catch validation errors raised by helpers and show them to the user
            _logger.error("Validation Error during Wallee refund for invoice %(invoice)s: %(error)s", {
                'invoice': self.name,
                'error': str(e)
            })
            # Re-raise to display the error message in the Odoo UI
            raise
        except (ValueError, AttributeError) as e:
            # Handle specific technical errors
            error_msg = f"Technical error during Wallee refund: {str(e)}"
            _logger.error(error_msg)
            raise UserError(_("A technical error occurred during the Wallee refund process: %(error)s", {'error': str(e)}))
