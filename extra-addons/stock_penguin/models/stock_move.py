# -*- coding: utf-8 -*-
from odoo import models
from odoo.tools import float_compare


class StockMove(models.Model):
    _inherit = 'stock.move'

    def _update_reserved_quantity(self, need, location_id,
                                  lot_id=None, package_id=None,
                                  owner_id=None, strict=True):
        rounding = self.product_id.uom_id.rounding
        if not strict:
            taken_quantity = super()._update_reserved_quantity(
                need=need, location_id=location_id, lot_id=lot_id,
                package_id=package_id, owner_id=owner_id, strict=True)
            if float_compare(taken_quantity, need, precision_rounding=rounding) == 0:
                return taken_quantity
        return super()._update_reserved_quantity(
                need=need, location_id=location_id, lot_id=lot_id,
                package_id=package_id, owner_id=owner_id, strict=strict)
