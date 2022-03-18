# -*- coding: utf-8 -*-
from odoo import models


# PEN-74: update pricelist and prices for client after logging in
class Website(models.Model):
    _inherit = 'website'

    def sale_get_order(self, force_create=False, code=None, update_pricelist=False, force_pricelist=False):
        partner_id = self.env.user.partner_id.commercial_partner_id
        if partner_id and partner_id.property_product_pricelist:
            return super().sale_get_order(
                force_create=force_create, code=code,
                update_pricelist=True, force_pricelist=partner_id.property_product_pricelist.id)
        return super().sale_get_order(force_create, code, update_pricelist, force_pricelist)
