from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    external_id = fields.Integer('External ID', copy=False)
    state = fields.Selection(selection_add=[
        ('future_sale', 'Future Sale'),
        ('future_sale_confirmation', 'Order Confirmation')
    ])


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    external_id = fields.Integer('External ID', copy=False)
