from odoo import models


class Website(models.Model):
    _inherit = 'website'

    def sale_get_order(self, *args, **kwargs):
        return super(Website, self.with_context(warehouse=self.sudo().company_id.warehouse_ids.ids)).sale_get_order(*args, **kwargs)

    def _get_product_available_qty(self, product):
        # override
        free_qty = 0
        warehouse_ids =  self.sudo().company_id.warehouse_ids
        for warehouse_id in warehouse_ids:
            free_qty += product.with_context(warehouse=warehouse_id.id).free_qty
        return free_qty
