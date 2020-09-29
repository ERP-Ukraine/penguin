from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    penguin_report_tmpl_calm = fields.Char('Calm, Report Tmpl')
