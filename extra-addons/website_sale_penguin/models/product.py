from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    website_sale_description = fields.Text(
        'Website Description', translate=True,
        help='A description of the Product that you want to show on your website')


class ProductPublicCategory(models.Model):
    _inherit = 'product.public.category'

    external_id = fields.Integer('External ID', copy=False)
