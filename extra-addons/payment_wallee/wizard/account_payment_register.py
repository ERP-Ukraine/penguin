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

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        invoice_id = self.env['account.move'].browse(self.env.context.get('active_id'))
        res.update({
            'is_wallee_refund': invoice_id.is_wallee_refund,
        })
        return res

    is_wallee_refund = fields.Boolean()

    def action_create_payments(self):
        if self.is_wallee_refund:
            return self._create_payments()
        return super().action_create_payments()

    def _create_payments(self):
        if self.is_wallee_refund:
            invoice = self.env['account.move'].browse(self.env.context.get('active_id'))
            amount_residual = invoice.amount_residual if invoice.amount_residual else self.amount_residual
            transactions = invoice.transaction_ids.filtered(
                lambda r: r.wallee_state in ['PENDING', 'PROCESSING', 'AUTHORIZED'] and r.provider_id.code == 'wallee')
            if transactions:
                raise UserError(
                    _('You have Payment Transactions that are not completed. Goto Payment Transactions and update the '
                      'status'))
            if self.amount > amount_residual:
                raise UserError(_('You are not allowed to refund more than the remaining amount'))
            refund_invoices = self.env['account.move'].search([
                ('id', '!=', invoice.id),
                ('is_wallee_active', '=', True),
                ('reversed_entry_id', '=', invoice.reversed_entry_id.id),
                ('state', '!=', 'cancel')])
            refund_amount = sum(inv.amount_total - inv.amount_residual for inv in refund_invoices)
            refund_amount += invoice.amount_total - amount_residual
            if self.amount > round(invoice.reversed_entry_id.amount_total - refund_amount, 2):
                raise UserError(_('You are not allowed to refund more than the amount in invoice'))
            invoice.is_wallee_active = True
            return invoice.action_wallee_refund()
        return super()._create_payments()
