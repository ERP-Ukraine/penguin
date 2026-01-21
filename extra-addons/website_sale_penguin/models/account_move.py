from odoo import fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    website_comment = fields.Char(string='Comment')
