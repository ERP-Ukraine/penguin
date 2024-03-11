# -*- coding: utf-8 -*-
from collections import defaultdict

from odoo import models
from odoo.addons.sale.models.payment_transaction import PaymentTransaction


class TransferPaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    # PEN-148: some parts of code here so that if something about penguin invoicing
    # policy changes, we could easily bring this code up

    def _process_feedback_data(self, data):
        # super()._process_feedback_data(data) some problem fix
        super()._send_payment_request()
        if self.provider != 'transfer':
            return

        if self.env['ir.config_parameter'].sudo().get_param('sale.automatic_invoice'):
            # Make transaction 'authorized' for manager to choose manually
            # when it's captured. After that generate invoice and post it
            self._set_authorized()

            # self._invoice_sale_orders()
            # self.invoice_ids.filtered(lambda inv: inv.state == 'draft').action_post()
        else:
            self._set_done()

    def _invoice_sale_orders(self):
        super(TransferPaymentTransaction, self.filtered(lambda t: t.provider != 'transfer'))._invoice_sale_orders()

        # if self.env['ir.config_parameter'].sudo().get_param('sale.automatic_invoice'):
        #     for trans in self.filtered(lambda t: t.sale_order_ids and t.provider != 'transfer'):
        #         trans = trans.with_company(trans.acquirer_id.company_id)\
        #             .with_context(company_id=trans.acquirer_id.company_id.id)
        #         # ERPU custom code
        #         confirmed_orders = trans.sale_order_ids.filtered(
        #             lambda so: so.state in ('sale', 'done') and not so.invoice_ids)
        #         # ERPU end of custom code
        #         if confirmed_orders:
        #             confirmed_orders._force_lines_to_invoice_policy_order()
        #             invoices = confirmed_orders._create_invoices()
        #             # Setup access token in advance to avoid serialization failure between
        #             # edi postprocessing of invoice and displaying the sale order on the portal
        #             for invoice in invoices:
        #                 invoice._portal_ensure_token()
        #             trans.invoice_ids = [(6, 0, invoices.ids)]

    # overriden from module 'sale' because there is no need to create
    # payment for wire transfer transactions it has to be created manually
    # def _reconcile_after_done(self):
    #     """ Override of payment to automatically confirm quotations and generate invoices. """
    #     draft_orders = self.sale_order_ids.filtered(lambda so: so.state in ('draft', 'sent'))
    #     for tx in self:
    #         tx._check_amount_and_confirm_order()
    #     confirmed_sales_orders = draft_orders.filtered(lambda so: so.state in ('sale', 'done'))
    #     # send order confirmation mail
    #     confirmed_sales_orders._send_order_confirmation_mail()
    #     # invoice the sale orders if needed

    #     # ERPU custom code
    #     self._invoice_sale_orders()
    #     if self.provider != 'transfer' or self.state == 'done':
    #         res = super(PaymentTransaction, self)._reconcile_after_done()
    #     else:
    #         res = self.invoice_ids.filtered(lambda inv: inv.state == 'draft').action_post()
    #     # ERPU end of custom code

    #     if self.env['ir.config_parameter'].sudo().get_param('sale.automatic_invoice') and any(so.state in ('sale', 'done') for so in self.sale_order_ids):
    #         self.filtered(lambda t: t.sale_order_ids.filtered(lambda so: so.state in ('sale', 'done')))._send_invoice()
    #     return res

    def _send_capture_request(self):
        super()._send_capture_request()
        if self.provider != 'transfer':
            return
        self._set_done()

    def _send_void_request(self):
        super()._send_void_request()
        if self.provider != 'transfer':
            return
        self._set_cancel()
