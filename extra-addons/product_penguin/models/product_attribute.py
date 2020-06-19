from odoo import fields, models


class ProductAttribute(models.Model):
    _inherit = 'product.attribute'

    external_id = fields.Integer('External ID', copy=False)


class ProductAttributeValue(models.Model):
    _inherit = 'product.attribute.value'

    external_id = fields.Integer('External ID', copy=False)
