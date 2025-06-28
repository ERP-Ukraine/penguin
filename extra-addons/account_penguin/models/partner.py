from odoo import fields, models


class AccountFiscalPosition(models.Model):
    _inherit = 'account.fiscal.position'

    external_id = fields.Integer('External ID', copy=False)
