# -*- coding: utf-8 -*-
from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    external_id = fields.Integer('External ID', copy=False)

    penguin_rrp_pc = fields.Monetary(string='RRP/pc', compute='_compute_penguin_rrp_pc')
    penguin_net_price_pc = fields.Monetary(string='Net Price/pc', compute='_compute_penguin_net_price_pc')

    def _compute_penguin_net_price_pc(self):
        for line in self:
            price_info = line.tax_id.compute_all(
                line.price_unit * (1 - (line.discount or 0.0) / 100.0),
                line.order_id.currency_id,
                1,  # quantity
                product=line.product_id,
                partner=line.order_id.partner_shipping_id,
            )
            line.penguin_net_price_pc = price_info['total_excluded']

    @api.depends('order_id.pricelist_id')
    def _compute_penguin_rrp_pc(self):
        for line in self:
            product = line.product_id
            pricelist_id = line.order_id.pricelist_id
                    
            if not pricelist_id:
                if line.currency_id == line.company_id.currency_id:
                    line.penguin_rrp_pc = product.lst_price
                else:
                    line.penguin_rrp_pc = line.currency_id._convert(
                        product.lst_price, line.company_id.currency_id,
                        line.company_id, line.order_id.date_order or fields.Date.today())
                continue
            products_qty_partner = [(
                product, line.product_uom_qty, line.order_partner_id
            )]
            results = pricelist_id._compute_price_rule(products_qty_partner)
            price, suitable_rule = results[product.id]
            if suitable_rule:
                item = self.env['product.pricelist.item'].browse(suitable_rule)
                if item.pricelist_id == pricelist_id and item.base == 'pricelist':
                    if line.currency_id == line.company_id.currency_id:
                        line.penguin_rrp_pc = product.with_context(pricelist=item.base_pricelist_id.id).price
                    else:
                        line.penguin_rrp_pc = line.currency_id._convert(
                            product.with_context(pricelist=item.base_pricelist_id.id).price, line.company_id.currency_id,
                            line.company_id, line.order_id.date_order or fields.Date.today())
                else:
                    if line.currency_id == line.company_id.currency_id:
                        line.penguin_rrp_pc = product.lst_price
                    else:
                        line.penguin_rrp_pc = line.currency_id._convert(
                            product.lst_price, line.company_id.currency_id,
                            line.company_id, line.order_id.date_order or fields.Date.today())
            else:
                if line.currency_id == line.company_id.currency_id:
                    line.penguin_rrp_pc = product.lst_price
                else:
                    line.penguin_rrp_pc = line.currency_id._convert(
                        product.lst_price, line.company_id.currency_id,
                        line.company_id, line.order_id.date_order or fields.Date.today())
