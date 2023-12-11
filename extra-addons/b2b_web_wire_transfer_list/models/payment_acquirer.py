from odoo import _, api, fields, models


class PaymentAcquirer(models.Model):
    _inherit = 'payment.acquirer'

    use_b2b_limitation = fields.Boolean()
    b2b_payment_partners = fields.Many2many('res.partner', string='Allow for partners')

    @api.model
    def _get_compatible_acquirers(
        self, company_id, partner_id, currency_id=None, force_tokenization=False,
        is_validation=False, **kwargs
    ):
        result = super()._get_compatible_acquirers(company_id, partner_id, currency_id=None, force_tokenization=False,
            is_validation=False, **kwargs)

        filtered_acquirers = self.env['payment.acquirer']

        for payment in result:
            if not payment.use_b2b_limitation or (payment.use_b2b_limitation and partner_id in payment.b2b_payment_partners.ids):
                filtered_acquirers |= payment

        return filtered_acquirers
