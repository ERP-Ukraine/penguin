# -*- coding: utf-8 -*-
import hashlib

from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    website_sale_description = fields.Text(
        'Website Description', translate=True,
        help='A description of the Product that you want to show on your website')
    hide_size_chart = fields.Boolean(default=False)
    functionality = fields.Text(
        translate=True,
        help='This field present in product page with tab name "Functionality"'
    )
    durability = fields.Text(
        translate=True,
        help='This field present in product page with tab name "Durability"'
    )


    def _get_first_product_variant(self, ptav):
        return self.env['product.product'].search([
            ('product_tmpl_id', '=', self.id),
            ('product_template_attribute_value_ids', 'in', ptav.id)
        ], limit=1)


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def get_unique(self):
        return hashlib.sha1(str(getattr(self, '__last_update')).encode('utf-8')).hexdigest()[0:7]


class ProductPublicCategory(models.Model):
    _inherit = 'product.public.category'

    external_id = fields.Integer('External ID', copy=False)
