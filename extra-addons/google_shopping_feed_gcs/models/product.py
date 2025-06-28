# -*- coding: utf-8 -*-
#!/usr/bin/python3
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging
import io
import base64
from urllib import parse
from PIL import Image

from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = "product.template"
    
    product_brand_id = fields.Many2one("product.brand.gsf", string="Product Brand", help="Product brand")
    gs_image_name = fields.Char(string="Google Shopping Image Name", help="Product google shopping image name.")

    
class ProductProduct(models.Model):
    _inherit = "product.product"
    
    @api.depends("image_1920", "product_tmpl_id.image_1920")
    def _compute_create_gsf_picture_url_gcs(self):
        for prod_img in self:
            sub_path = ""
            if prod_img.image_1920:
                data = io.BytesIO(base64.standard_b64decode(prod_img.image_1920))
                img = Image.open(data)
                parsed_name = parse.quote((prod_img.name).replace("/", "-"))
                sub_path = "/web/image/product.product/%s/image_1920/%s.%s" % (
                prod_img.id, parsed_name, img.format.lower())
            prod_img.write({'gs_image_url_gcs': sub_path})
    
    gs_image_url_gcs = fields.Char(string="Google Shopping Image URL", compute="_compute_create_gsf_picture_url_gcs",
                               store=True, help="Product google shopping image URL")
    
    def _get_images_gsf(self, gsf_account_id):
        """Return a list of records implementing `image.mixin` to
        display on the carousel on the website for this variant.

        This returns a list and not a recordset because the records might be
        from different models (template, variant and image).

        It contains in this order: the main image of the variant (if set), the
        Variant Extra Images, and the Template Extra Images.
        """
        self.ensure_one()
        images_list = []
        if not gsf_account_id.gs_website_domain:
            return images_list
        
        images = self.product_variant_image_ids + self.product_template_image_ids
        for i in images:
            images_list.append(gsf_account_id.gs_website_domain + i.gs_image_url)
        
        images_list = [gsf_account_id.gs_website_domain + self.gs_image_url_gcs] + images_list
        return images_list
