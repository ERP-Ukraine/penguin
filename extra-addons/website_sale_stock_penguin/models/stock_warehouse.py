from odoo import _, api, fields, models


class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    country_id = fields.Many2one(
        'res.country',
        help='When choosing the warehouse from which the goods are to be shipped,'
             ' the warehouse located in the same country as the customer will be'
             ' selected first. Works only with multi warehouse option on'
    )
