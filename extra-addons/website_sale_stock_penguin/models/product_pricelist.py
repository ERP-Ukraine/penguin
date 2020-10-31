from odoo import models, fields


class ProductPricelist(models.Model):
    _inherit = 'product.pricelist'

    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse')
    salesperson_id = fields.Many2one('res.users', string='Sales Person')
