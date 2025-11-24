# -*- coding: utf-8 -*-
from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    website_comment = fields.Char(string='Comment')

    def _prepare_invoice(self):
        """Copy website_comment from SO to invoice."""
        invoice_vals = super()._prepare_invoice()
        if self.website_comment:
            invoice_vals['website_comment'] = self.website_comment
        return invoice_vals
