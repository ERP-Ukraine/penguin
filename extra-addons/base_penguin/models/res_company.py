from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    external_id = fields.Integer('External ID', copy=False)
