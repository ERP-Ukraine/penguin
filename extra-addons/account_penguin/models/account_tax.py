# -*- coding: utf-8 -*-

from odoo import api, models


class AccountTax(models.Model):
    _inherit = 'account.tax'

    @api.model
    def _fix_tax_included_price(self, price, prod_taxes, line_taxes):
        return price
