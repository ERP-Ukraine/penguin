from odoo.addons.website_sale.controllers.main import WebsiteSale

from odoo import http
from odoo.http import request


class PenguinWebsiteSale(WebsiteSale):
    def _get_search_order(self, post):
        if post:
            return super()._get_search_order(post)
        else:
            return 'is_published desc, list_price desc, id desc'


class ShopComment(WebsiteSale):
    @http.route(['/shop/comment'], type='http', auth="public", website=True, sitemap=False)
    def comment(self, comment, **post):
        redirect = post.get('r', '/shop/cart')
        if comment:
            sale_order = request.website.sale_get_order()
            if sale_order:
                sale_order.website_comment = comment
            return request.redirect(redirect)
