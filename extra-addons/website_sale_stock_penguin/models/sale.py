# -*- coding: utf-8 -*-

from odoo import api, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'


    @api.onchange('pricelist_id')
    def _onchange_pricelist_id(self):
        if self.pricelist_id.warehouse_id:
            self.warehouse_id = self.pricelist_id.warehouse_id
