from odoo import http
from odoo.http import request

from odoo.addons.sale.controllers.variant import VariantController


def filter_product_virtual_available(product):
    return product.website_published and product.virtual_available > 0 and product.free_qty > 0


class WebsiteSaleStockPenguinVariantController(VariantController):
    @http.route(['/sale/get_all_published_combinations_website'], type='json', auth='public', methods=['POST'], website=True)
    def get_all_published_combinations_website(self, product_template_id, product_template_attribute_value_id, **kw):
        warehouse_ids = request.website.sudo().warehouse_ids.ids
        pt = request.env['product.template'].sudo().with_context(warehouse=warehouse_ids).browse(int(product_template_id))
        ptav = request.env['product.template.attribute.value'].browse(int(product_template_attribute_value_id))
        product_variants_color = pt._get_possible_variants().filtered(lambda p: ptav in p.product_template_variant_value_ids)
        available_sizes = product_variants_color.filtered(filter_product_virtual_available)
        return available_sizes.product_template_attribute_value_ids.ids
