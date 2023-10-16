from odoo import models
from odoo.tools import float_compare, float_is_zero


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def _get_multi_warehouse_procurements(self, line, product_qty, procurement_uom, values, precision, warehouse_ids=None):
        if not warehouse_ids:
            return [
                self.env['procurement.group'].Procurement(
                    line.product_id, product_qty, procurement_uom,
                    line.order_id.partner_shipping_id.property_stock_customer,
                    line.product_id.display_name, line.order_id.name, line.order_id.company_id, values)
            ]
        procurements = []
        for warehouse_id in warehouse_ids:
            if float_compare(product_qty, 0, precision_digits=precision) != 1:
                return procurements
            warehouse_qty = line.product_id.with_context(warehouse=warehouse_id.id).free_qty
            # skip this warehouse if there is no product free qty
            if float_compare(warehouse_qty, 0, precision_digits=precision) != 1:
                continue
            qty_delta = float_compare(warehouse_qty, product_qty, precision_digits=precision)
            reserved_qty = product_qty if qty_delta != -1 else warehouse_qty
            # create new values dictionary for new warehouse because
            # it holds reference to same values object
            values = {**values, 'warehouse_id': warehouse_id}
            procurements.append(self.env['procurement.group'].Procurement(
                line.product_id, reserved_qty, procurement_uom,
                line.order_id.partner_shipping_id.property_stock_customer,
                line.product_id.display_name, line.order_id.name, line.order_id.company_id, values))
            product_qty -= reserved_qty
        return procurements

    # override to create different pickings depending on warehouse
    def _action_launch_stock_rule(self, previous_product_uom_qty=False):
        """
        Launch procurement group run method with required/custom fields genrated by a
        sale order line. procurement group will launch '_run_pull', '_run_buy' or '_run_manufacture'
        depending on the sale order line product rule.
        """
        if self._context.get("skip_procurement"):
            return True
        # ERPUkraine get all warehouses from order website
        warehouse_ids = self.sudo().company_id.warehouse_ids
        # ERPUkraine end of custom code
        precision = self.env['decimal.precision'].precision_get(
            'Product Unit of Measure')
        procurements = []
        for line in self:
            line = line.with_company(line.company_id)
            if line.state != 'sale' or not line.product_id.type in ('consu', 'product'):
                continue
            qty = line._get_qty_procurement(previous_product_uom_qty)
            if float_compare(qty, line.product_uom_qty, precision_digits=precision) == 0:
                continue

            group_id = line._get_procurement_group()
            if not group_id:
                group_id = self.env['procurement.group'].create(
                    line._prepare_procurement_group_vals())
                line.order_id.procurement_group_id = group_id
            else:
                # In case the procurement group is already created and the order was
                # cancelled, we need to update certain values of the group.
                updated_vals = {}
                if group_id.partner_id != line.order_id.partner_shipping_id:
                    updated_vals.update(
                        {'partner_id': line.order_id.partner_shipping_id.id})
                if group_id.move_type != line.order_id.picking_policy:
                    updated_vals.update(
                        {'move_type': line.order_id.picking_policy})
                if updated_vals:
                    group_id.write(updated_vals)

            values = line._prepare_procurement_values(group_id=group_id)

            product_qty = line.product_uom_qty - qty

            line_uom = line.product_uom
            quant_uom = line.product_id.uom_id
            product_qty, procurement_uom = line_uom._adjust_uom_quantities(
                product_qty, quant_uom)
            # ERPUkraine check qty in all available warehouses if needed
            procurements.extend(self._get_multi_warehouse_procurements(
                line, product_qty, procurement_uom, values, precision, warehouse_ids)
            )
            # ERPUkraine end of custom code
        if procurements:
            self.env['procurement.group'].run(procurements)

        # This next block is currently needed only because the scheduler trigger is done by picking confirmation rather than stock.move confirmation
        orders = self.mapped('order_id')
        for order in orders:
            pickings_to_confirm = order.picking_ids.filtered(
                lambda p: p.state not in ['cancel', 'done'])
            if pickings_to_confirm:
                # Trigger the Scheduler for Pickings
                pickings_to_confirm.action_confirm()
        return True
