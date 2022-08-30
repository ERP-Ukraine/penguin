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
