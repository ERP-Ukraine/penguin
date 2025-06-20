from odoo.upgrade import util


def migrate(cr, version):
    util.remove_record(cr, 'sale_penguin.mail_template_sale_confirmation')
