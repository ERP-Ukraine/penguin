from odoo import _, api, fields, models


class PaymenProvider(models.Model):
    _inherit = 'payment.provider'

    use_b2b_limitation = fields.Boolean()
    b2b_payment_partners = fields.Many2many('res.partner', string='Allow for partners')

    @api.model
    def _get_compatible_providers(
        self, company_id, partner_id, amount, currency_id=None, force_tokenization=False,
        is_express_checkout=False, is_validation=False, **kwargs
    ):
        result = super()._get_compatible_providers(company_id, partner_id, amount, currency_id=None, force_tokenization=False,
        is_express_checkout=False, is_validation=False, **kwargs)

        filtered_providers = self.env['payment.provider']
        for payment in result:
            if not payment.use_b2b_limitation or (payment.use_b2b_limitation and partner_id in payment.b2b_payment_partners.ids):
                filtered_providers |= payment

        return filtered_providers
