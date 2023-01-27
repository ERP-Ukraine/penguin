from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    website_warehouse_ids = fields.Many2many(
        'stock.warehouse',
        readonly=False,
        related='website_id.warehouse_ids',
        domain="[('company_id', '=', website_company_id)]",
    )
