from odoo.upgrade import util


def migrate(cr, version):
    util.remove_view(cr, xml_id='website_sale_penguin.main_categories', silent=False)
    util.remove_view(cr, xml_id='website_sale_penguin.sub_categories', silent=False)
    util.remove_view(cr, xml_id='website_sale_penguin.penguin_product', silent=False)
    util.remove_view(cr, xml_id='website_sale_penguin.product_price', silent=False)
    util.remove_view(cr, xml_id='website_sale_penguin.shop_product_carousel', silent=False)
    util.remove_view(cr, xml_id='website_sale_penguin.color_picker', silent=False)
    util.remove_view(cr, xml_id='website_sale_penguin.penguin_products_item', silent=False)
    util.remove_view(cr, xml_id='website_sale_penguin.penguin_products', silent=False)
    util.remove_view(cr, xml_id='website_sale_penguin.comment_form', silent=False)
    util.remove_view(cr, xml_id='website_sale_penguin.website_comment_template', silent=False)
    util.remove_view(cr, xml_id='website_sale_penguin.confirmation_with_comment', silent=False)
    util.remove_view(cr, xml_id='website_sale_penguin.pricelist_list', silent=False)
    util.remove_view(cr, xml_id='website_sale_penguin.template_header_default_website', silent=False)
    util.remove_view(cr, xml_id='website_sale_penguin.template_header_default_website_sale', silent=False)
