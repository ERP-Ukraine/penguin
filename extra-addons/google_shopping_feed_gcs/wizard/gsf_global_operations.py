# -*- coding: utf-8 -*-
#!/usr/bin/python3
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import models, fields, api, _

class GoogleShoppingProcessImportExport(models.TransientModel):
    _name = 'google.shopping.process.import.export'
    _description = "Google Shopping Import Export Process"

            
    gsf_account_id = fields.Many2one("google.shopping.feed.account", "Google Shopping Account")
    instance_ids = fields.Many2many("google.shopping.feed.instance", 'google_shopping_import_export_rel', 'process_id', 'instance_id',
                                    "Google Shopping Instances", required=True)
    
    gsf_import_export_type = fields.Selection([
        ('import_sync', 'Import/Sync.'),
        ('export_update', 'Export/Update')
    ], string="Operation Type", help="Select operation type")
    gsf_sub_operation_type1 = fields.Selection(selection=[
        ('import_products', 'Import Products'),
        ('get_product_status', 'Get Product Status')
    ], string="Operation Sub Type", help="Select operation sub type")
    gsf_sub_operation_type2 = fields.Selection(selection=[
        ('export_products', 'Export Products'),
        ('update_products', 'Update Products'),
        ('update_inventory_informations', 'Update Product Inventory Informations'),
    ], string="Operation Sub Type", help="Select operation sub type")
    
    @api.onchange('gsf_account_id')
    def _change_account_to_make_empty(self):
        for rec in self:
            rec.instance_ids = False
            rec.gsf_import_export_type = False
            rec.gsf_sub_operation_type1 = False
            rec.gsf_sub_operation_type2 = False
    
    @api.onchange('instance_ids')        
    def _change_instances_to_make_empty(self):
        for rec in self:
            rec.gsf_import_export_type = False
            rec.gsf_sub_operation_type1 = False
            rec.gsf_sub_operation_type2 = False
       
    @api.onchange('gsf_import_export_type')        
    def _change_gsf_import_export_type_to_make_empty(self):
        for rec in self:
            rec.gsf_sub_operation_type1 = False
            rec.gsf_sub_operation_type2 = False

    def prepare_product_for_export_to_gsf(self):
        gsf_product_variant_obj = self.env['google.shopping.product.variants']
        template_active_ids = self._context.get('active_ids', [])
        product_template_ids = self.env['product.template'].search(
            [('id', 'in', template_active_ids), ('type', '!=', 'service')])
        
        for instance in self.instance_ids:
            gs_account_id = instance.gs_account_id
            gs_website_id = gs_account_id.gs_website_id
            
            for product_template in product_template_ids:
                for product_variant in product_template.product_variant_ids:
                    if not product_variant.default_code:
                        continue
                    
                    if product_variant.website_id and (gs_website_id.id != product_variant.website_id.id):
                        continue 
                    
                    google_shopping_product_variant = gsf_product_variant_obj.search(
                        [('gs_instance_id', '=', instance.id), ('odoo_product_id', '=', product_variant.id)], limit=1)
                    
                    product_title = ""
                    attribute_values_name = product_variant.product_template_attribute_value_ids and " (%s)" %(", ".join(product_variant.product_template_attribute_value_ids.mapped('display_name'))) or ""
                    
                    if attribute_values_name: 
                        product_title = product_variant.name + attribute_values_name
                    else:
                        product_title = product_variant.name
                    
                    if not google_shopping_product_variant:
                        vals = {
                            'gs_instance_id': instance.id, 'odoo_product_id': product_variant.id,
                            'name': product_title,
                            'offer_id': product_variant.default_code or '',
                            'description': product_variant.description_sale,
                            'channel': 'online',
                            'brand': product_variant.product_brand_id and product_variant.product_brand_id.id or False,
                            'shipping_weight': product_variant.weight,
                            'availability': 'in_stock',
                            'product_condition': 'new',
                            'gtin': product_variant.barcode
                        }
                        gsf_product_variant_obj.create(vals)
                    else:
                        vals = {
                            'name': product_title,
                            'offer_id': product_variant.default_code or '',
                            'description': product_variant.description_sale,
                            'brand': product_variant.product_brand_id and product_variant.product_brand_id.id or False,
                            'shipping_weight': product_variant.weight,
                            'gtin': product_variant.barcode
                        }
                        google_shopping_product_variant.write(vals)
        return True

    def action_execute(self):
        if self.gsf_import_export_type == "import_sync":
            # Google Shopping to Odoo
            if self.gsf_sub_operation_type1 == "import_products":
                # Import product
                self.import_google_shopping_products()
            elif self.gsf_sub_operation_type1 == "get_product_status":
                # Get Product Status
                self.get_product_status_from_google_shopping()
        elif self.gsf_import_export_type == "export_update":
            # Odoo to Google Shopping
            if self.gsf_sub_operation_type2 == "export_products":
                # Export products
                self.export_products_in_google_shopping()
            elif self.gsf_sub_operation_type2 == "update_products":
                # Update products
                self.update_products_in_google_shopping()
            elif self.gsf_sub_operation_type2 == "update_inventory_informations":
                # Update inventory informations
                self.update_products_inventory_info()
        return True
    
    
    def export_products_in_google_shopping(self):
        """
            This method call to export products of the selected instances.
            :return: True or Error
        """
        gsf_product_variants_obj = self.env['google.shopping.product.variants']
        
        instances = self.instance_ids
        shopping_products = gsf_product_variants_obj.search([
            ('exported_in_google_shopping', '=', False),
            ('gs_instance_id.state', '=', 'confirmed'),
            ('gs_instance_id', 'in', instances.ids)
        ])
        if shopping_products:
            shopping_products.export_products_in_google_shopping()
        return True    
    
    def update_products_in_google_shopping(self):
        """
            This method call to update exported products of the selected instances.
            :return: True or Error
        """
        gsf_product_variants_obj = self.env['google.shopping.product.variants']
        
        instances = self.instance_ids
        shopping_products = gsf_product_variants_obj.search([
            ('exported_in_google_shopping', '=', True),
            ('gs_instance_id.state', '=', 'confirmed'),
            ('gs_instance_id', 'in', instances.ids),
            ('google_product_id', '!=', '')
        ])
        if shopping_products:
            shopping_products.update_products_in_google_shopping()
        return True    
    
    def import_google_shopping_products(self):
        """
            This method call to import google shopping products of the selected instances and account.
            :return: True or Error
        """
        gsf_product_variants_obj = self.env['google.shopping.product.variants']
        instances = self.instance_ids
        gsf_account_id = self.gsf_account_id
        gsf_product_variants_obj.import_google_shopping_products(instances, gsf_account_id)
        return True

    def get_product_status_from_google_shopping(self):
        """
            This method call to import google shopping products of the selected instances and account.
            :return: True or Error
        """
        gsf_product_variants_obj = self.env['google.shopping.product.variants']
        instances = self.instance_ids
        shopping_products = gsf_product_variants_obj.search([
            ('exported_in_google_shopping', '=', True),
            ('gs_instance_id.state', '=', 'confirmed'),
            ('gs_instance_id', 'in', instances.ids),
            ('google_product_id', '!=', '')
        ])
        shopping_products and shopping_products.get_product_status_from_google_shopping()
        return True
    
    def update_products_inventory_info(self):
        """
            This method call to update exported products inventory info of the selected instances.
            :return: True or Error
        """
        gsf_product_variants_obj = self.env['google.shopping.product.variants']
        
        instances = self.instance_ids
        shopping_products = gsf_product_variants_obj.search([
            ('exported_in_google_shopping', '=', True),
            ('gs_instance_id.state', '=', 'confirmed'),
            ('gs_instance_id', 'in', instances.ids),
            ('google_product_id', '!=', '')
        ])
        shopping_products and shopping_products.update_product_inventory_info()
        return True    
    
            
        