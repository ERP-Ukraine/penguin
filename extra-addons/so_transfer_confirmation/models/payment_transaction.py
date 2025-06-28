from odoo import models


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    def _set_pending(self, state_message=None):
        super()._set_pending(state_message)

        for record in self:
            sales_orders = record.sale_order_ids.filtered(lambda so: so.state in ['draft', 'sent'])
            sales_orders.filtered(lambda so: so.state == 'draft').with_context(tracking_disable=True).write({'state': 'sent'})

            if record.payment_method_code == 'wire_transfer':
                for so in record.sale_order_ids:
                    so.action_confirm()
                    so._create_invoices()
