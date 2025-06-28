from odoo import _, api, fields, models
from datetime import timedelta


class LoyaltyGenerateWizard(models.TransientModel):
    _inherit = "loyalty.generate.wizard"
    valid_until = fields.Date(
        default=lambda self: fields.Date.context_today(self) + timedelta(days=365)
    )
