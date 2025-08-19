from odoo import fields, models, api


class Warehouse(models.Model):
    _inherit = 'stock.warehouse'

    ffn_id = fields.Char(string='FFN ID')
    delivery_carrier_ids = fields.Many2many('delivery.carrier')
