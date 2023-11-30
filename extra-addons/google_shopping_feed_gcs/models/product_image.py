# -*- coding: utf-8 -*-
#!/usr/bin/python3
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import io
import base64
from urllib import parse
from PIL import Image

from odoo import models, fields, api

 
class ProductImage(models.Model):
    _inherit = "product.image"
    
    @api.depends("image_1920")
    def _compute_create_gsf_picture_url_gcs(self):
        for prod_img in self:
            sub_path = ""
            if prod_img.image_1920:
                data = io.BytesIO(base64.standard_b64decode(prod_img.image_1920))
                img = Image.open(data)
                parsed_name = parse.quote((prod_img.name).replace("/", "-"))
                sub_path = "/web/image/product.image/%s/image_1920/%s.%s" % (
                prod_img.id, parsed_name, img.format.lower())
            prod_img.write({'gs_image_url': sub_path})
        
    gs_image_name = fields.Char(string="Google Shopping Image Name", help="Product google shopping image name.")
    gs_image_url = fields.Char(string="Google Shopping Image URL", compute="_compute_create_gsf_picture_url_gcs",
                               store=True, help="Product google shopping image URL")
