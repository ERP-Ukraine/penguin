# -*- coding: utf-8 -*-
from collections import defaultdict

from odoo import models
from odoo.addons.sale.models.payment_transaction import PaymentTransaction


class TransferPaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    def _process_feedback_data(self, data):
        super()._send_payment_request()
        if self.provider != 'transfer':
            return

        if self.env['ir.config_parameter'].sudo().get_param('sale.automatic_invoice'):
            # Do not confirm TX if invoice autocreation is enabled
            # as it will create invoice, payment and send paid invoice via email
            # however real payment is not received yet
            self._set_authorized()
        else:
            self._set_done()

    # overriden from module 'sale' because there is no need to create
    # payment for wire transfer transactions it has to be created manually
    def _reconcile_after_done(self):
        """ Override of payment to automatically confirm quotations and generate invoices. """
        draft_orders = self.sale_order_ids.filtered(lambda so: so.state in ('draft', 'sent'))
        for tx in self:
            tx._check_amount_and_confirm_order()
        confirmed_sales_orders = draft_orders.filtered(lambda so: so.state in ('sale', 'done'))
        # send order confirmation mail
        confirmed_sales_orders._send_order_confirmation_mail()
        # invoice the sale orders if needed
        self._invoice_sale_orders()

        # ERPU custom code
        if self.provider == 'transfer':
            res = self.invoice_ids.filtered(lambda inv: inv.state == 'draft').action_post()
        else:
            res = super(PaymentTransaction, self)._reconcile_after_done()
        # ERPU end of custom code

        if self.env['ir.config_parameter'].sudo().get_param('sale.automatic_invoice') and any(so.state in ('sale', 'done') for so in self.sale_order_ids):
            self.filtered(lambda t: t.sale_order_ids.filtered(lambda so: so.state in ('sale', 'done')))._send_invoice()
        return res

    def _send_capture_request(self):
        super()._send_capture_request()
        if self.provider != 'transfer':
            return

        self._set_done()
        self._finalize_post_processing()
        self._execute_callback()

    def _send_void_request(self):
        super()._send_void_request()
        if self.provider != 'transfer':
            return
        self._set_cancel()
