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
            and partner_id.specific_property_product_pricelist
        ):
            pricelist = partner_id.specific_property_product_pricelist
            parent_id = partner_id.parent_id

            if parent_id and parent_id.specific_property_product_pricelist:
                pricelist = parent_id.specific_property_product_pricelist

            request.session['website_sale_current_pl'] = pricelist.id
            request.session['website_sale_selected_pl_id'] = pricelist.id
        return super().sale_get_order(*args, **kwargs)

    def get_pricelist_available(self, show_visible=False):
        partner_id = self.env.user.partner_id.commercial_partner_id
        if (
            partner_id
            and self.env.user._is_portal()
            and partner_id.specific_property_product_pricelist
        ):
            pricelist = partner_id.specific_property_product_pricelist
            parent_id = partner_id.parent_id

            if parent_id and parent_id.specific_property_product_pricelist:
                pricelist = parent_id.specific_property_product_pricelist
            return pricelist

        return super().get_pricelist_available(show_visible=show_visible)
