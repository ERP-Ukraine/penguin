from odoo import fields, models, api


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    ffn_id = fields.Char(string='FFN ID')
    partner_id = fields.Many2one('res.partner', string='Fulfiller')
