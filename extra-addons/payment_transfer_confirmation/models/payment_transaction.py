# -*- coding: utf-8 -*-
from collections import defaultdict

from odoo import models


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

    def _reconcile_after_done(self):
        if self.provider != 'transfer':
            return super()._reconcile_after_done()
        self.invoice_ids.filtered(lambda inv: inv.state == 'draft').action_post()

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
