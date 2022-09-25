from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    arnold_report_id = fields.Many2one('sale.order.arnold.report')
