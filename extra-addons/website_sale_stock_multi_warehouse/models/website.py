from odoo import fields, models


class Website(models.Model):
    _inherit = 'website'

    def sale_get_order(self, *args, **kwargs):
        return super(Website, self.with_context(warehouse=self.sudo().company_id.warehouse_ids.ids)).sale_get_order(*args, **kwargs)
