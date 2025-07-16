from odoo.upgrade import util


def migrate(cr, version):
    util.remove_view(cr, xml_id='website_penguin.penguin_frontend_layout', silent=False)
    util.remove_view(cr, xml_id='website_penguin.penguin_pager', silent=False)
    util.remove_view(cr, xml_id='website_penguin.penguin_footer', silent=False)
    util.remove_view(cr, xml_id='website_penguin.template_header_default', silent=False)
    util.remove_view(cr, xml_id='website_penguin.placeholder_header_call_to_action', silent=False)
    util.remove_view(cr, xml_id='website_penguin.header_language_selector', silent=False)
    util.remove_view(cr, xml_id='website_penguin.language_selector', silent=False)
    util.remove_view(cr, xml_id='website_penguin.footer_copyright_company_name', silent=False)
