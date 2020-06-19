from odoo import fields, models


class ProductPublicCategory(models.Model):
    _inherit = 'product.public.category'

    external_id = fields.Integer('External ID', copy=False)
