from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    address_country_group_ids = fields.Many2many(
        related='website_id.address_country_group_ids',
        string='Address Country Groups',
        readonly=False
    )
