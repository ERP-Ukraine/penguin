# -*- coding: utf-8 -*-
import logging

from odoo import fields, models
from odoo.http import request

_logger = logging.getLogger(__name__)


# PEN-74: update pricelist and prices for client after logging in
class Website(models.Model):
    _inherit = 'website'

    address_country_group_ids = fields.Many2many(
        'res.country.group', string='Address Country Groups'
    )

    def sale_get_order(self, *args, **kwargs):
        partner_id = self.env.user.partner_id.commercial_partner_id
        if (
            partner_id
            and self.env.user._is_portal()
            and partner_id.property_product_pricelist
        ):
            request.session['website_sale_current_pl'] = (
                partner_id.property_product_pricelist.id
            )
            request.session['website_sale_selected_pl_id'] = (
                partner_id.property_product_pricelist.id
            )
        return super().sale_get_order(*args, **kwargs)

    def get_pricelist_available(self, show_visible=False):
        partner_id = self.env.user.partner_id.commercial_partner_id
        if (
            partner_id
            and self.env.user._is_portal()
            and partner_id.property_product_pricelist
        ):
            return partner_id.property_product_pricelist
        return super().get_pricelist_available(show_visible=False)
