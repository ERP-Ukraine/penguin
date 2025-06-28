from odoo import api, fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    external_id = fields.Integer('External ID', copy=False)
