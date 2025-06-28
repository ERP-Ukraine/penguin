# -*- coding: utf-8 -*-
#!/usr/bin/python3
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import models, fields, api
from odoo.exceptions import Warning

 
class GoogleShoppingProductImages(models.Model):
    _name = "google.shopping.product.images"
    _description = "Google Shopping Product Images"
         
    name = fields.Char("Product Name", required=True)
    gs_product_variant_id = fields.Many2one("google.shopping.product.variants",
                                            string="Google Shopping Product Variant")
    product_image = fields.Binary(string="Product Image", attachment=True)
    product_image_full_name = fields.Char(string="Product Image Name", help="Product image full name.")
    image_url = fields.Char(string="Image URL", help="Product image URL")
    is_main_image = fields.Boolean("Is Main Image?", default=False, help="Main gallery image")
 
    @api.model
    def create(self, vals):
        image_id = super(GoogleShoppingProductImages, self).create(vals)
        base_path = self.env['ir.config_parameter'].get_param('web.base.url')
        sub_path = "/image/google.shopping.product.images/%s/product_image/%s" % (image_id.id,
                                                                                  image_id.product_image_full_name)
        image_id.write({'image_url': base_path + sub_path})
        return image_id
     
    def write(self, vals):
        base_path = self.env['ir.config_parameter'].get_param('web.base.url')
        sub_path = "/image/google.shopping.product.images/%s/product_image/%s" % (self.id,
                                                                                vals.get('product_image_full_name',
                                                                                self.product_image_full_name))
        vals.update({'image_url': base_path + sub_path})
        return super(GoogleShoppingProductImages, self).write(vals)
