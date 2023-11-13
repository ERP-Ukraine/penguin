from odoo import models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    # PEN-201: independent sales for Arnold Sports
    def _get_multi_warehouse_procurements(self, line, product_qty, procurement_uom, values, precision, warehouse_ids=None):
        arnold_id_config = self.env['ir.config_parameter'].sudo().get_param('sale_arnoldsports.arnold_partner_id')
        arnold_partner_id = self.env['res.partner'].sudo().search([('id', '=', arnold_id_config)], limit=1)

        if self.order_partner_id == arnold_partner_id:
            arnold_warehouse_config = self.env['ir.config_parameter'].sudo().get_param('sale_arnoldsports.arnold_warehouse_id')
            arnold_warehouse_id = self.env['stock.warehouse'].sudo().search([('id', '=', arnold_warehouse_config)], limit=1)
            warehouse_ids = arnold_warehouse_id

        return super()._get_multi_warehouse_procurements(line, product_qty, procurement_uom, values, precision, warehouse_ids)
