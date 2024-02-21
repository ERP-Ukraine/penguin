from odoo import _, api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    manual_sale_for_arnold = fields.Boolean(string="Manual Sale")
    hide_manual_arnold_sale = fields.Boolean(compute="_compute_hide_manual_arnold_sale")

    @api.depends("partner_id")
    def _compute_hide_manual_arnold_sale(self):
        for order in self:
            arnold_id_config = self.env['ir.config_parameter'].sudo().get_param('sale_arnoldsports.arnold_partner_id')
            arnold_partner_id = self.env['res.partner'].sudo().search([('id', '=', arnold_id_config)], limit=1)
            if arnold_partner_id == order.partner_id:
                order.hide_manual_arnold_sale = False
            else:
                order.hide_manual_arnold_sale = True
