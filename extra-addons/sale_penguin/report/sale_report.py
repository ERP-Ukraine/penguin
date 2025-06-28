from odoo import fields, models


class SaleReport(models.Model):
    _inherit = 'sale.report'

    state = fields.Selection(selection_add=[
        ('future_sale', 'Pre-ordered'),
        ('future_sale_confirmation', 'Pre-order confirmed'),
    ])
