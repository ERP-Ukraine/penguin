# -*- coding: utf-8 -*-
from odoo import api, fields, models


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    sale_order_id = fields.Many2one('sale.order', compute='_compute_sale_order_fields',
                                    string='Sale Order', store=True)
    sale_partner_name = fields.Char(compute='_compute_sale_order_fields',
                                    string='Customer', store=True)

    @api.depends('move_id')
    def _compute_sale_order_fields(self):
        for line in self:
            line.sale_order_id = line.move_id.sale_line_id.order_id
            line.sale_partner_name = line.sale_order_id.partner_id.name
