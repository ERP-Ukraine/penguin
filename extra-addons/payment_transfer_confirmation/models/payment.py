# -*- coding: utf-8 -*-
from collections import defaultdict

from odoo import models


class TransferPaymentAcquirer(models.Model):
    _inherit = 'payment.acquirer'

    def _get_feature_support(self):
        res = super()._get_feature_support()
        res['authorize'].append('transfer')
        return res


class TransferPaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    def _transfer_form_validate(self, data):
        if self.env['ir.config_parameter'].sudo().get_param('sale.automatic_invoice'):
            # Do not confirm TX if invoice autocreation is enabled
            # as it will create invoice, payment and send paid invoice via email
            # however real payment is not received yet
            self._set_transaction_authorized()
        else:
            self._set_transaction_done()
            self.execute_callback()
        return True

    def transfer_s2s_capture_transaction(self):
        self._set_transaction_done()
        self.execute_callback()
        #_reconcile_after_transaction_done
        invoices = self.mapped('invoice_ids').filtered(lambda inv: inv.state == 'draft')
        invoices.post()

        # Create & Post the payments.
        payments = defaultdict(lambda: self.env['account.payment'])
        for trans in self:
            if trans.payment_id:
                payments[trans.acquirer_id.company_id.id] += trans.payment_id
                continue

            payment_vals = trans._prepare_account_payment_vals()
            payment = self.env['account.payment'].create(payment_vals)
            payments[trans.acquirer_id.company_id.id] += payment

            # Track the payment to make a one2one.
            trans.payment_id = payment

        for company in payments:
            payments[company].with_context(force_company=company, company_id=company).post()

        if not payments:
            self._post_process_after_done()
        else:
            self.write({'is_processed': True})

    def transfer_s2s_void_transaction(self):
        self._set_transaction_cancel()
