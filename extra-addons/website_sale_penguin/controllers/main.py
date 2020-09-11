from odoo.addons.website_sale.controllers.main import WebsiteSale


class PenguinWebsiteSale(WebsiteSale):
    def _get_search_order(self, post):
        if post:
            return super()._get_search_order(post)
        else:
            return 'is_published desc, list_price desc, id desc'
