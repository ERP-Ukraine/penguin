# -*- coding: utf-8 -*-
from odoo import http
from odoo.addons.website_sale.controllers.main import WebsiteSale


class PenguinWebsiteSale(WebsiteSale):
    def _get_search_order(self, post):
        if post:
            return super()._get_search_order(post)
        else:
            return 'is_published desc, list_price desc, id desc'

    @http.route(['/shop/comment'], type='http', auth="public", website=True, sitemap=False)
    def comment(self, comment, **post):
        redirect = post.get('r', '/shop/cart')
        if comment:
            sale_order = http.request.website.sale_get_order()
            if sale_order:
                sale_order.website_comment = comment
            return http.request.redirect(redirect)

    @http.route('/shop/payment', type='http', auth='public', website=True, sitemap=False)
    def shop_payment(self, **post):
        http.request.session['check_partner_country'] = True
        return super().shop_payment(**post)

    def _get_country_related_render_values(self, kw, render_values):
        res = super()._get_country_related_render_values(kw, render_values)
        address_countries = http.request.website.address_country_group_ids.country_ids
        if address_countries:
            res['countries'] = res['countries'].filtered(lambda c: c.id in address_countries.ids)
        return res
