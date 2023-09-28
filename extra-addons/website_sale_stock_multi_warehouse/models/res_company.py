from odoo import fields, models


class Company(models.Model):
    _inherit = "res.company"

    warehouse_ids = fields.Many2many(
        'stock.warehouse', string='Available Warehouses')
