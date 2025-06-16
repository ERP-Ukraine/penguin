# -*- coding: utf-8 -*-

from odoo import api, models


class AccountTax(models.Model):
    _inherit = 'account.tax'

    @api.model
    def _fix_tax_included_price(self, price, prod_taxes, line_taxes):
        prod_taxes = prod_taxes._origin
        line_taxes = line_taxes._origin
        incl_tax = prod_taxes.filtered(lambda tax: tax not in line_taxes and tax.price_include)
        # if incl_tax:  # original line
        if incl_tax and not all(line_taxes.mapped('price_include')):    # ERPU line
            # if tax on line is not default(from product)
            # and it is not price included as well
            return incl_tax.compute_all(price)['total_excluded']
        return price

    @api.model
    def _adapt_price_unit_to_another_taxes(self, price_unit, product, original_taxes, new_taxes):
        if (original_taxes == new_taxes or False in original_taxes.mapped('price_include')
            # ERPU begin
            or len(new_taxes) != 1 or new_taxes.amount != 0.0):
            # ERPU end
            return price_unit

        taxes_computation = original_taxes._get_tax_details(
            price_unit,
            1.0,
            rounding_method='round_globally',
            product=product,
        )
        price_unit = taxes_computation['total_excluded']

        taxes_computation = new_taxes._get_tax_details(
            price_unit,
            1.0,
            rounding_method='round_globally',
            product=product,
            special_mode='total_excluded',
        )
        delta = sum(x['tax_amount'] for x in taxes_computation['taxes_data'] if x['tax'].price_include)
        return price_unit + delta

