from odoo import models
from odoo.tools import float_compare


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def _create_procurements(self, product_qty, procurement_uom, origin, values):
        self.ensure_one()
        # override by ERPUkraine to get all warehouses from order website
        warehouse_ids = self.sudo().company_id.warehouse_ids.sorted(
            key=lambda warehouse: 0 if warehouse == self.order_id.warehouse_id else 1
        )
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')

        if not warehouse_ids:
            return super()._create_procurements(product_qty, procurement_uom, origin, values)

        # logic for multi warehouse procurements
        procurements = []
        for num, warehouse_id in enumerate(warehouse_ids):
            if float_compare(product_qty, 0, precision_digits=precision) != 1:
                return procurements
            warehouse_qty = self.product_id.with_context(warehouse=warehouse_id.id).free_qty
            # skip this warehouse if there is no product free qty
            if float_compare(warehouse_qty, 0, precision_digits=precision) != 1:
                # add products without balances to be able to backorder later
                if num == (len(warehouse_ids) - 1) and not procurements:
                    return [
                        self.env['procurement.group'].Procurement(
                            self.product_id,
                            product_qty,
                            procurement_uom,
                            self._get_location_final(),
                            self.product_id.display_name,
                            origin,
                            self.order_id.company_id,
                            values,
                        )
                    ]
                continue
            qty_delta = float_compare(warehouse_qty, product_qty, precision_digits=precision)
            reserved_qty = product_qty if qty_delta != -1 else warehouse_qty
            # create new values dictionary for new warehouse because
            # it holds reference to same values object
            values = {**values, 'warehouse_id': warehouse_id}
            procurements.append(
                self.env['procurement.group'].Procurement(
                    self.product_id,
                    reserved_qty,
                    procurement_uom,
                    self._get_location_final(),
                    self.product_id.display_name,
                    origin,
                    self.order_id.company_id,
                    values,
                )
            )
            product_qty -= reserved_qty
        return procurements
