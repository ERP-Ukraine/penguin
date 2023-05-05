# -*- coding: utf-8 -*-
import logging

from odoo import fields, models, http
from odoo.exceptions import UserError
from odoo.tests.common import Form

_logger = logging.getLogger(__name__)


# PEN-74: update pricelist and prices for client after logging in
class Website(models.Model):
    _inherit = 'website'

    address_country_group_ids = fields.Many2many('res.country.group', string='Address Country Groups')

    def _get_selectable_pricelist_domain(self, currency_name='CHF'):
        return [
            ('name', '=', currency_name),
            ('currency_id', '=', self.env.ref('base.%s' % currency_name).id),
            ('selectable', '=', True)
        ]

    def _get_country_pricelist(self, order):
        europe_cg = self.env['res.country.group'].with_context(lang='en_US').search([('name', '=', 'Europe')], limit=1)
        if not europe_cg:
            _logger.warning('Could not find "Europe" country group, partner\'s country check not working properly')
        partner_country = order.partner_id.country_id
        use_pricelist_chf = not europe_cg or partner_country not in europe_cg.country_ids
        domain = self._get_selectable_pricelist_domain('CHF' if use_pricelist_chf else 'EUR')
        return self.env['product.pricelist'].search(domain, limit=1)

    def sale_get_order(self, force_create=False, code=None, update_pricelist=False, force_pricelist=False):
        order = super().sale_get_order(force_create, code, update_pricelist, force_pricelist)
        if order.state != 'draft':
            return order

        # personal pricelist check for b2b customers
        domain = self._get_selectable_pricelist_domain()
        default_pl = self.env['product.pricelist'].search(domain, limit=1)
        personal_pl = self.env.user.partner_id.commercial_partner_id.property_product_pricelist
        if default_pl != personal_pl and order.pricelist_id != personal_pl:
            return super(Website, self.with_context(personal_pricelist_set=True)).sale_get_order(
                force_create=force_create,
                code=code,
                update_pricelist=True,
                force_pricelist=personal_pl.id
            )

        if self._context.get('personal_pricelist_set'):
            return order

        # checking if partners country has different pricelist
        new_pricelist = False
        if http.request.session.pop('check_partner_country', None):
            new_pricelist = self._get_country_pricelist(order)

        if new_pricelist and order.pricelist_id != new_pricelist:
            return super().sale_get_order(
                force_create=force_create,
                code=code,
                update_pricelist=True,
                force_pricelist=new_pricelist.id
            )
        return order

    def _prepare_sale_order_values(self, partner, pricelist):
        # Set Sales Person from Contact's form
        # Fallback to Website's Sales person
        values = super()._prepare_sale_order_values(partner, pricelist)
        default_user_id = partner.parent_id.user_id.id or partner.user_id.id
        if default_user_id:
            values['user_id'] = default_user_id
        return values
