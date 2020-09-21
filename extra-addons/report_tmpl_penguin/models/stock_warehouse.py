from odoo import fields, models


class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    penguin_report_tmpl_iban = fields.Char('IBAN, Penguin Template')
    penguin_report_tmpl_acc_nr = fields.Char('Acc. Nr., Penguin Template')
    penguin_report_tmpl_swift = fields.Char('Swift, Penguin Template')
