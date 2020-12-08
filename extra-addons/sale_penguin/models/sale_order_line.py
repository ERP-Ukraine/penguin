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

    def _get_fallback_rrp_pricelist(self):
        # We assume that public pricelist for website has retail prices
        self.ensure_one()
        order_currency = self.order_id.pricelist_id.currency_id
        domain = [('currency_id', '=', order_currency.id), ('selectable', '=', True)]
        return self.env['product.pricelist'].search(domain, limit=1)

    def _get_parent_rrp_pricelist(self):
        # Return pricelist that is used as base
        # for current pricelist's formula
        # or empty record otherwise.
        self.ensure_one()
        Pricelist = self.env['product.pricelist']
        pricelist_id = self.order_id.pricelist_id
        if not pricelist_id:
            return Pricelist
        results = pricelist_id._compute_price_rule([(self.product_id, self.product_uom_qty,
                                                     self.order_partner_id)])
        price, suitable_rule = results[self.product_id.id]
        if suitable_rule:
            item = self.env['product.pricelist.item'].browse(suitable_rule)
            if item.pricelist_id == pricelist_id and item.base == 'pricelist':
                return item.base_pricelist_id
        return Pricelist

    @api.depends('order_id.pricelist_id')
    def _compute_penguin_rrp_pc(self):
        for line in self:
            rrp_pricelist = line._get_parent_rrp_pricelist()
            if not rrp_pricelist:
                rrp_pricelist = line._get_fallback_rrp_pricelist()
            rrp_pc = line.product_id.with_context(pricelist=rrp_pricelist.id).price
            if line.currency_id != rrp_pricelist.currency_id:
                # convert to Order currency
                fx_date = line.order_id.date_order or fields.Date.today()
                rrp_pc = rrp_pricelist.currency_id._convert(rrp_pc, line.currency_id,
                                                            line.company_id, fx_date)
            line.penguin_rrp_pc = rrp_pc
