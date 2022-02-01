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
