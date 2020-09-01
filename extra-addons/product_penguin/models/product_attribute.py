from odoo import fields, models
from odoo.http import request


class ProductAttribute(models.Model):
    _inherit = 'product.attribute'

    external_id = fields.Integer('External ID', copy=False)


class ProductAttributeValue(models.Model):
    _inherit = 'product.attribute.value'

    external_id = fields.Integer('External ID', copy=False)


class ProductTemplateAttributeValue(models.Model):
    _inherit = 'product.template.attribute.value'

    website_published = fields.Boolean('Website Published', default=True)

    def _only_active(self):
        if request and getattr(request, 'website', False):
            return self.filtered(lambda ptav: ptav.ptav_active and ptav.website_published)
        return super()._only_active()
