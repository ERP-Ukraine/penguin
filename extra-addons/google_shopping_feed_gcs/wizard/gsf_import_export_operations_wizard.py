# -*- coding: utf-8 -*-
#!/usr/bin/python3
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import models, fields


class GoogleShoppingProductWizard(models.TransientModel):
    _name = 'google.shopping.product.wizard'
    _description = "Google Shopping Product Wizard"
    
    def export_products_in_google_shopping(self):
        google_shopping_product_variants = self.env['google.shopping.product.variants']
        active_ids = self._context.get('active_ids', [])
        
        if active_ids:
            shopping_poducts = google_shopping_product_variants.search([
                ('id', 'in', active_ids),
                ('exported_in_google_shopping', '=', False),
                ('gs_instance_id.state', '=', 'confirmed')
            ])
            shopping_poducts and shopping_poducts.export_products_in_google_shopping()
        return True
    
    def update_products_in_google_shopping(self):
        google_shopping_product_variants = self.env['google.shopping.product.variants']
        active_ids = self._context.get('active_ids', [])
        
        if active_ids:
            shopping_poducts = google_shopping_product_variants.search([
                ('id', 'in', active_ids),
                ('exported_in_google_shopping', '=', True),
                ('gs_instance_id.state', '=', 'confirmed'),
                ('google_product_id', '!=', '')
            ])
            shopping_poducts and shopping_poducts.update_products_in_google_shopping()
        return True
    
    def import_google_shopping_products_by_id(self):
        google_shopping_product_variants = self.env['google.shopping.product.variants']
        active_ids = self._context.get('active_ids', [])
        if active_ids:
            shopping_poducts = google_shopping_product_variants.search([
                ('id', 'in', active_ids),
                ('exported_in_google_shopping', '=', True),
                ('gs_instance_id.state', '=', 'confirmed'),
                ('google_product_id', '!=', '')
            ])
            shopping_poducts and shopping_poducts.import_google_shopping_products_by_id()
        return True
    
    def delete_google_shopping_products_by_id(self):
        google_shopping_product_variants = self.env['google.shopping.product.variants']
        active_ids = self._context.get('active_ids', [])
        
        if active_ids:
            shopping_poducts = google_shopping_product_variants.search([
                ('id', 'in', active_ids),
                ('exported_in_google_shopping', '=', True),
                ('gs_instance_id.state', '=', 'confirmed'),
                ('google_product_id', '!=', ''),
                ('active', 'in', [True, False])
            ])
            shopping_poducts and shopping_poducts.delete_google_shopping_products_by_id()
        return True
    
    def update_products_inventory_info_in_google_shopping(self):
        google_shopping_product_variants = self.env['google.shopping.product.variants']
        active_ids = self._context.get('active_ids', [])
        
        if active_ids:
            shopping_poducts = google_shopping_product_variants.search([
                ('id', 'in', active_ids),
                ('exported_in_google_shopping', '=', True),
                ('gs_instance_id.state', '=', 'confirmed'),
                ('google_product_id', '!=', '')
            ])
            shopping_poducts and shopping_poducts.update_product_inventory_info()
        return True
    
    def get_product_status_from_google_shopping(self):
        google_shopping_product_variants = self.env['google.shopping.product.variants']
        active_ids = self._context.get('active_ids', [])
        
        if active_ids:
            shopping_poducts = google_shopping_product_variants.search([
                ('id', 'in', active_ids),
                ('exported_in_google_shopping', '=', True),
                ('gs_instance_id.state', '=', 'confirmed'),
                ('google_product_id', '!=', '')
            ])
            shopping_poducts and shopping_poducts.get_product_status_from_google_shopping()
        return True