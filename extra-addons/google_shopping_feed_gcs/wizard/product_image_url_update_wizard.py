# -*- coding: utf-8 -*-
#!/usr/bin/python3
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import models, fields


class ProductImageURLUpdateWizard(models.TransientModel):
    _name = 'product.image.url.update.wizard'
    _description = "Product Image URL Update Wizard"
    
    start_db_id = fields.Integer("Start DB ID")
    end_db_id = fields.Integer("end DB ID") 
    
    def update_extra_product_media_urls(self):
        """Re-update extra product media URLs.
        
        @author: GCS
        @return: True
        """
        product_images = self.env['product.image'].search([("id", ">=", self.start_db_id),
                                                           ("id", "<=", self.end_db_id)], order="id asc")
        for product_image in product_images:
            product_image._compute_create_gsf_picture_url_gcs()
            product_image._cr.commit()
        return True
    
    def update_product_profile_image_url(self):
        """Re-update product main profile image URL.
        
        @author: GCS
        @return: True
        """
        _domain = [('detailed_type', 'in', ['product', 'consu']),
                   ("id", ">=", self.start_db_id),
                   ("id", "<=", self.end_db_id)]
        product_variants = self.env['product.product'].search(_domain, order="id asc")
        for product_variant in product_variants:
            product_variant._compute_create_gsf_picture_url_gcs()
            product_variant._cr.commit()
        return True
