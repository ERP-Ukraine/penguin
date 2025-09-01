from datetime import datetime

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_verified = fields.Boolean(default=True)
    create_date = fields.Datetime(default=datetime.now())
