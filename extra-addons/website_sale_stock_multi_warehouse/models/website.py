from odoo import fields, models


class Website(models.Model):
    _inherit = 'website'

    warehouse_ids = fields.Many2many('stock.warehouse', string='Available Warehouses')

    def sale_get_order(self, *args, **kwargs):
        return super(Website, self.with_context(warehouse=self.sudo().warehouse_ids.ids)).sale_get_order(*args, **kwargs)

