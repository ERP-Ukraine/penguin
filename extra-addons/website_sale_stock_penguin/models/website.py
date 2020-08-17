from odoo import models


class Website(models.Model):
    _inherit = 'website'

    def sale_get_order(self, *args, **kwargs):
        sale_order = super().sale_get_order(*args, **kwargs)
        pricelist_warehouse_id = sale_order.pricelist_id.warehouse_id
        if pricelist_warehouse_id and sale_order.warehouse_id != pricelist_warehouse_id:
            sale_order.write({'warehouse_id': pricelist_warehouse_id.id})
        return sale_order
