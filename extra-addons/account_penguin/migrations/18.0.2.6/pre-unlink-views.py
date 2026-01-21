from odoo.upgrade import util

def migrate(cr, version):
    util.remove_view(cr, xml_id='account_penguin.view_move_form_website_comment_penguin')
