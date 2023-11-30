# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import datetime
import json
import logging
import time
import pytz

from odoo import models, fields, api, _

from odoo.addons.google_shopping_feed_gcs.google_shopping_api.google_shopping_api import GoogleShoppingAPI

_logger = logging.getLogger(__name__)


class GoogleShoppingProductVariants(models.Model):
    _name = "google.shopping.product.variants"
    _description = "Google Shopping Variants"

    name = fields.Char(string='Product Name', required=True, help="Product name")
    gs_instance_id = fields.Many2one("google.shopping.feed.instance", string="Shopping Instance", help="Instance")
    gs_account_id = fields.Many2one("google.shopping.feed.account", related="gs_instance_id.gs_account_id", store=True,
                                    string="Shopping Account", help="Account")
    gs_website_id = fields.Many2one("website", related="gs_account_id.gs_website_id", string="Website",
                                    help="Select website")
    odoo_product_id = fields.Many2one("product.product", "Odoo Product Variant", help="Odoo product variant")
    odoo_product_tmpl_id = fields.Many2one("product.template", related="odoo_product_id.product_tmpl_id",
                                           string="Odoo Product Template", store=True, help="Odoo product template")

    google_product_id = fields.Char("Google Product ID", help="Google Product ID")
    offer_id = fields.Char("Offer ID", help="Google Offer ID (Internal Reference)")
    description = fields.Char("Description", help="Product description")
    # ('local', 'Local'),
    channel = fields.Selection([
        ('online', 'Online'),
    ], string="Channel")
    brand = fields.Many2one("product.brand.gsf", "Product Brand")
    gtin = fields.Char("GTIN", help="Global Trade Item Number (GTIN) of the item.")
    mpn = fields.Char("MPN", help="Manufacturer Part Number (MPN) of the item.")
    # price = fields.Float(string="Price", help="Price of the item.")
    product_shop_link = fields.Char("Product Shop Link", related="odoo_product_id.website_url",
                                    help="Product shop link.")
    shipping_weight = fields.Float("Shipping Weight")
    shipping_height = fields.Float("Shipping Height")
    shipping_width = fields.Float("Shipping Width")
    shipping_length = fields.Float("Shipping Length")
    availability = fields.Selection([
        ('in_stock', 'In Stock'),
        ('out_of_stock', 'Out of Stock'),
    ], string="Product Availability")
    product_condition = fields.Selection([
        ('new', 'New'),
        ('refurbished', 'Refurbished'),
        ('used', 'Used'),
    ], string="Product Condition",
        help="New: Brand new, original, unopened packaging, Refurbished: Professionally restored to working order, \
            comes with a warranty, may or may not have the original packaging, Used: Previously used, original \
            packaging opened or missing")
    exported_in_google_shopping = fields.Boolean("Exported in Google Shopping?")
    active_product_in_google_shopping = fields.Boolean("Active in Google Shopping?")
    stock_type = fields.Selection([('fix', 'Fix'), ('percentage', 'Percentage')], string='Fix Stock Type')
    stock_value = fields.Float(string='Fix Stock Value')
    product_status = fields.Char(string="Product Google Status", help="Product status of the Google Shopping")
    product_expiration_date = fields.Datetime(string="Product Expiration Date",
                                              help="Product expired at this date in Google Shopping")
    active = fields.Boolean('Active', related="odoo_product_id.active", store=True,
                            help="If unchecked, it will allow you to hide the product without removing it.")

    def _calculate_product_tax_price(self, gsf_instance, product_price):
        tax_price = 0.0
        if gsf_instance.product_price_with_tax and gsf_instance.product_price_account_tax:
            tax_id = gsf_instance.product_price_account_tax
            tax_vals = tax_id.compute_all(product_price)
            tax_price = sum(t.get('amount', 0.0) for t in tax_vals.get('taxes', []))
        return tax_price

    def prepare_product_dict(self):
        """
            This method use to prepare product dict for export/update product in Google Shopping.
            :Return: dict
        """

        gsf_instance = self.gs_instance_id
        gsf_account_id = self.gs_account_id
        odoo_product_id = self.odoo_product_id

        product_shop_link = gsf_account_id.gs_website_domain + self.product_shop_link
        # category_trail = self.odoo_product_id.categ_id.name_get()[0][1].replace(" / ", " > ") if (
        #    self.odoo_product_id.categ_id) else ""
        category_trail = (odoo_product_id.google_product_category and
                          odoo_product_id.google_product_category.complete_name or "")
        offer_pricelist = gsf_instance.offer_pricelist
        lang_code = gsf_instance.language and gsf_instance.language.iso_code[:2] or ""

        vals = {
            "contentLanguage": lang_code,
            "targetCountry": gsf_instance.country_id and gsf_instance.country_id.code[:2] or "",
            "googleProductCategory": category_trail,
            "title": self.name,
            "offerId": self.offer_id,
            "description": self.description,
            "link": product_shop_link,
            "channel": self.channel,
            "availability": "in stock" if self.availability == "in_stock" else "out of stock",
            "brand": self.brand and self.brand.name or "",
            "condition": self.product_condition
        }
        self.gtin and vals.update({"gtin": self.gtin})
        self.gtin and vals.update({"mpn": self.mpn})

        product_price = self.odoo_product_id.with_context({
            "pricelist": gsf_instance.pricelist.id,
            "quantity": 1
        }).price
        tax_price = self._calculate_product_tax_price(gsf_instance, product_price)
        product_price = product_price and round(product_price + tax_price, 2) or 0.00

        vals["price"] = {
            "value": product_price,
            "currency": gsf_instance.pricelist.currency_id.name
        }

        if offer_pricelist:
            offer_line_price_rule = offer_pricelist.get_product_price_rule(product=self.odoo_product_id,
                                                                           quantity=1, partner=False)
            pricelist_rule_line = offer_line_price_rule and offer_pricelist.item_ids.filtered(lambda x:
                                                                                              x.id ==
                                                                                              offer_line_price_rule[
                                                                                                  1]) or False
            offer_price = offer_line_price_rule and round(
                offer_line_price_rule[0] + self._calculate_product_tax_price(gsf_instance, offer_line_price_rule[0]),
                2) or product_price

            if pricelist_rule_line and pricelist_rule_line.date_start and pricelist_rule_line.date_end:
                offer_startdate = pricelist_rule_line.date_start.astimezone(pytz.utc)
                offer_enddate = pricelist_rule_line.date_end.astimezone(pytz.utc)
                current_date = datetime.datetime.now().astimezone(pytz.utc)

                if offer_startdate <= current_date <= offer_enddate:
                    final_offer_start_date = offer_startdate.strftime("%Y-%m-%dT%H:%MZ")
                    final_offer_end_date = offer_enddate.strftime("%Y-%m-%dT%H:%MZ")
                    sale_price_effective_date = "%s/%s" % (final_offer_start_date, final_offer_end_date)
                    vals.update({
                        "sale_price": {
                            "value": offer_price,
                            "currency": offer_pricelist.currency_id.name
                        },
                        "sale_price_effective_date": sale_price_effective_date
                    })
                else:
                    vals.update({
                        "sale_price": {
                            "value": offer_price,
                            "currency": offer_pricelist.currency_id.name
                        },
                        "sale_price_effective_date": ""
                    })

            else:
                vals.update({
                    "sale_price": {
                        "value": offer_price,
                        "currency": offer_pricelist.currency_id.name
                    },
                    "sale_price_effective_date": ""
                })

        images = self.odoo_product_id._get_images_gsf(gsf_account_id)
        if images:
            vals.update({
                "imageLink": images[0],
                "additionalImageLinks": images[1:10]
            })
        if gsf_account_id.stock_field:
            product_stock = self.get_google_shopping_product_stock(self, gsf_account_id.warehouse_ids,
                                                                   gsf_account_id.stock_field.name)
        else:
            product_stock = self.get_google_shopping_product_stock(self, gsf_account_id.warehouse_ids, "")
        vals.update({"sellOnGoogleQuantity": round(product_stock, 2)})
        return vals

    def export_products_in_google_shopping(self):
        """
            This method use to Export Product in Google Shopping.
            :Return: True or Error
        """
        google_shopping_log_book = self.env['google.shopping.feed.log.tracker']
        google_shopping_log_book_line_obj = self.env['google.shopping.feed.log.line.tracker']
        GoogleShoppingAPIObj = GoogleShoppingAPI()

        gsf_log_tracker_id = False
        for product in self:
            gs_account_id = self.gs_account_id
            instance = self.gs_instance_id

            product_dict = product.prepare_product_dict()
            response_obj = GoogleShoppingAPIObj.export_product_in_gsf_api(gs_account_id, product_dict)
            if response_obj.status_code in [401]:
                _logger.info("Call: Export products, Reason: Expired Access Token, Status Code: 401")
                gs_account_id.get_gsf_refresh_tokens()
                response_obj = GoogleShoppingAPIObj.export_product_in_gsf_api(gs_account_id, product_dict)
            if response_obj.status_code == 200:
                response_vals = response_obj.json()
                vals = {
                    'offer_id': response_vals.get('offerId'),
                    'google_product_id': response_vals.get('id'),
                    'exported_in_google_shopping': True,
                    'active_product_in_google_shopping': True if response_vals.get('channel') == 'online' else False,
                }
                product.write(vals)
            elif response_obj.status_code in [400, 403]:
                if not gsf_log_tracker_id:
                    value = {
                        'gs_instance_id': instance.id,
                        'log_message': 'Export Product to google shopping.',
                        'operation_sub_type': 'export_product',
                        'operation_type': 'export',
                        'is_skip_process': True
                    }
                    gsf_log_tracker_id = google_shopping_log_book.create(value)
                log_line_vals = {
                    'record_reference': product.name,
                    'gsf_log_tracker_id': gsf_log_tracker_id.id,
                    'log_type': 'error',
                    'action_type': 'skip_line',
                    'operation_type': 'export',
                    'message': response_obj.json(),
                }
                google_shopping_log_book_line_obj.create(log_line_vals)
            self._cr.commit()
        return True

    def update_products_in_google_shopping(self):
        """
        This method used to create Update Product Queues.
        
        @author: Grow Consultancy Services
        @return: True or Error
        """
        update_product_data_queue_gcs_obj = self.env['update.product.data.queue.gcs']
        update_product_data_queue_line_gcs_obj = self.env['update.product.data.queue.line.gcs']
        instance_wise_counter_dict, instance_wise_queue_dict = self.prepare_instance_wise_counter_queue()
        update_product_queue = False
        update_product_queue_list = []
        for product in self:
            gs_instance_id = product.gs_instance_id
            if instance_wise_counter_dict[gs_instance_id] == 200:
                update_product_queue = update_product_data_queue_gcs_obj.create({
                    'gs_instance_id': gs_instance_id.id
                })
                instance_wise_queue_dict[gs_instance_id] = update_product_queue
                update_product_queue_list.append(update_product_queue.id)
                message = "Product Queue Created %s" % update_product_queue.name
                update_product_queue.generate_sendone_notification(message)
                self._cr.commit()
                instance_wise_counter_dict[gs_instance_id] = 1
            #
            product_dict = product.prepare_product_dict()
            update_product_data_queue_line_gcs_obj.create({
                "product_offer_id": product_dict.get("offerId"),
                "name": product_dict.get("title"),
                "synced_product_response": json.dumps(product_dict),
                "update_product_data_queue_id": update_product_queue and update_product_queue.id or False,
            })
            instance_wise_counter_dict[gs_instance_id] = instance_wise_counter_dict[gs_instance_id] + 1
            self._cr.commit()
        return True

    def auto_process_update_product_queues(self):
        """
        This method use to Update Product in Google Shopping.
        @author: Grow Consultancy Services
        @return: True or Error
        """
        update_product_data_queue_gcs_obj = self.env['update.product.data.queue.gcs']
        update_product_queue_ids = []
        query = """
            SELECT queue.id
            FROM update_product_data_queue_line_gcs AS queue_line
            INNER JOIN update_product_data_queue_gcs AS queue on queue_line.update_product_data_queue_id = queue.id
            WHERE queue_line.state='draft'
            ORDER BY queue_line.create_date ASC
        """
        self._cr.execute(query)
        update_product_queue_list = self._cr.fetchall()
        if not update_product_queue_list:
            return True

        for result in update_product_queue_list:
            if result[0] not in update_product_queue_ids:
                update_product_queue_ids.append(result[0])

        queues = update_product_data_queue_gcs_obj.browse(update_product_queue_ids)
        self.filter_update_product_queue_lines_and_post_message_and_process_queue(queues)
        return True

    def filter_update_product_queue_lines_and_post_message_and_process_queue(self, queues):
        """
        @author: Grow Consultancy Services
        @return: True or Error
        """
        for queue in queues:
            update_product_data_queue_lines = queue.update_product_data_queue_lines.filtered(
                lambda x: x.state == "draft")
            self.process_update_product_queue(update_product_data_queue_lines)

    def process_update_product_queue(self, update_product_data_queue_lines):
        """
        This method use to Update Product in Google Shopping.
        @author: Grow Consultancy Services
        @return: True or Error
        """
        google_shopping_log_book = self.env['google.shopping.feed.log.tracker']
        google_shopping_log_book_line_obj = self.env['google.shopping.feed.log.line.tracker']
        GoogleShoppingAPIObj = GoogleShoppingAPI()

        gsf_log_tracker_id = False
        for queue_line in update_product_data_queue_lines:
            gs_account_id = queue_line.gs_account_id
            gs_instance_id = queue_line.gs_instance_id
            product_dict = json.loads(queue_line.synced_product_response)
            queue_id = queue_line.update_product_data_queue_id

            response_obj = GoogleShoppingAPIObj.update_product_in_google_shopping_api(gs_account_id, product_dict)
            if response_obj.status_code in [401]:
                _logger.info("Call: Update products, Reason: Expired Access Token, Status Code: 401")
                gs_account_id.get_gsf_refresh_tokens()
                response_obj = GoogleShoppingAPIObj.update_product_in_google_shopping_api(gs_account_id, product_dict)

            product = self.search([('offer_id', '=', queue_line.product_offer_id),
                                   ('gs_account_id', '=', gs_account_id.id),
                                   ('gs_instance_id', '=', gs_instance_id.id)], limit=1)
            if response_obj.status_code == 200:
                response_vals = response_obj.json()
                vals = {
                    'offer_id': response_vals.get('offerId'),
                    'google_product_id': response_vals.get('id'),
                    'exported_in_google_shopping': True,
                    'active_product_in_google_shopping': True if response_vals.get('channel') == 'online' else False,
                }
                product.write(vals)
                queue_line.write({'state': 'done'})
            elif response_obj.status_code == 400:
                if not gsf_log_tracker_id:
                    value = {
                        'gs_instance_id': gs_instance_id.id,
                        'log_message': 'Update Product to google shopping.',
                        'operation_sub_type': 'update_product',
                        'operation_type': 'update',
                        'is_skip_process': True
                    }
                    gsf_log_tracker_id = google_shopping_log_book.create(value)
                    queue_id.write({'log_tracker': gsf_log_tracker_id.id})
                log_line_vals = {
                    'record_reference': product.name,
                    'gsf_log_tracker_id': gsf_log_tracker_id.id,
                    'log_type': 'error',
                    'action_type': 'skip_line',
                    'operation_type': 'export',
                    'message': response_obj.json(),
                    'update_product_data_queue_line_id': queue_line.id
                }
                google_shopping_log_book_line_obj.create(log_line_vals)
                queue_line.write({'state': 'failed'})
            self._cr.commit()
        return True

    def get_google_shopping_product_stock(self, shopping_product, warehouse_ids, stock_type='virtual_available'):
        actual_stock = 0.0
        odoo_product = shopping_product.odoo_product_id
        product = self.env['product.product'].with_context(warehouse=warehouse_ids.ids).browse(odoo_product.id)
        if hasattr(product, str(stock_type)):
            actual_stock = getattr(product, stock_type)
        else:
            actual_stock = product.qty_available

        minimum_stock = []
        is_mrp_installed = self.env['ir.module.module'].search([('name', '=', 'mrp'), ('state', '=', 'installed')])
        if is_mrp_installed:
            bom_product = self.env['mrp.bom'].sudo()._bom_find(products=product)
        else:
            bom_product = False
        if bom_product:
            bom_product_line_ids = self.get_bom_product_component_lines(product, quantity=1)
            for bom_line, line in bom_product_line_ids:
                bom_comp_product_stock = getattr(bom_line.product_id, stock_type) if hasattr(
                    bom_line.product_id,
                    str(stock_type)) else bom_line.product_id.qty_available
                actual_stock = int(bom_comp_product_stock / bom_line.product_qty)
                minimum_stock.append(actual_stock)
            actual_stock = minimum_stock and min(minimum_stock) or 0

        if actual_stock >= 1.00:
            if shopping_product.stock_type == 'fix':
                if shopping_product.stock_value >= actual_stock:
                    return actual_stock
                else:
                    return shopping_product.stock_value

            elif shopping_product.stock_type == 'percentage':
                quantity = int(actual_stock * shopping_product.stock_value)
                if quantity >= actual_stock:
                    return actual_stock
                else:
                    return quantity
        return actual_stock

    def get_bom_product_component_lines(self, product, quantity):
        try:
            bom_obj = self.env['mrp.bom']
            bom_point = bom_obj.sudo()._bom_find(products=product)
            from_uom = product.uom_id
            to_uom = bom_point.get(product).product_uom_id
            factor = from_uom._compute_quantity(quantity, to_uom) / bom_point.get(product).product_qty
            bom, lines = bom_point.get(product).explode(product, factor,
                                                        picking_type=bom_point.get(product).picking_type_id)
            return lines
        except BaseException as e:
            return []

    def import_google_shopping_products_by_id(self):
        """
            This method use to Import Product Info by ID from Google Shopping.
            :Return: True or Error
        """
        google_shopping_log_book = self.env['google.shopping.feed.log.tracker']
        google_shopping_log_book_line_obj = self.env['google.shopping.feed.log.line.tracker']
        product_brand_gsf_obj = self.env['product.brand.gsf']
        GoogleShoppingAPIObj = GoogleShoppingAPI()

        gsf_log_tracker_id = False
        for product in self:
            gs_account_id = self.gs_account_id
            instance = self.gs_instance_id
            google_product_id = product.google_product_id

            response_obj = GoogleShoppingAPIObj.import_product_info_from_gsf_by_id_api(gs_account_id, google_product_id)
            if response_obj.status_code in [401]:
                _logger.info("Call: Import products, Reason: Expired Access Token, Status Code: 401")
                gs_account_id.get_gsf_refresh_tokens()
                response_obj = GoogleShoppingAPIObj.import_product_info_from_gsf_by_id_api(gs_account_id,
                                                                                           google_product_id)

            if response_obj.status_code == 200:
                response_vals = response_obj.json()
                vals = {
                    'exported_in_google_shopping': True,
                    'active_product_in_google_shopping': True if response_vals.get('channel') == 'online' else False,
                    'description': response_vals.get('description'),
                    'product_condition': response_vals.get('condition'),
                    'name': response_vals.get('title'),
                    'gtin': response_vals.get('gtin'),
                    'mpn': response_vals.get('mpn'),
                    'product_shop_link': response_vals.get('link'),
                    'channel': response_vals.get('channel'),
                }
                if response_vals.get('availability') == "in stock":
                    vals.update({'availability': 'in_stock'})
                elif response_vals.get('availability') == "out of stock":
                    vals.update({'availability': 'out_of_stock'})

                if response_vals.get('brand'):
                    brand_id = product_brand_gsf_obj.search([('name', '=ilike', response_vals.get('brand'))], limit=1)
                    brand_id and vals.update({'brand': brand_id.id})

                product.write(vals)
            elif response_obj.status_code == 400:
                if not gsf_log_tracker_id:
                    value = {
                        'gs_instance_id': instance.id,
                        'log_message': 'Import Product from google shopping.',
                        'operation_sub_type': 'import_product',
                        'operation_type': 'import',
                        'is_skip_process': True
                    }
                    gsf_log_tracker_id = google_shopping_log_book.create(value)
                log_line_vals = {
                    'record_reference': product.name,
                    'gsf_log_tracker_id': gsf_log_tracker_id.id,
                    'log_type': 'error',
                    'action_type': 'skip_line',
                    'operation_type': 'import',
                    'message': response_obj.json(),
                }
                google_shopping_log_book_line_obj.create(log_line_vals)
            elif response_obj.status_code == 404:
                response = response_obj.json()
                error_list = response.get('error', {}).get('errors', [])
                if error_list and error_list[0].get("reason") == "notFound":
                    vals = {
                        'exported_in_google_shopping': False,
                        'active_product_in_google_shopping': False,
                    }
                    product.write(vals)
            self._cr.commit()
        return True

    def delete_google_shopping_products_by_id(self):
        """
            This method use to Delete products by ID from Google Shopping.
            :Return: True or Error
        """
        google_shopping_log_book = self.env['google.shopping.feed.log.tracker']
        google_shopping_log_book_line_obj = self.env['google.shopping.feed.log.line.tracker']
        GoogleShoppingAPIObj = GoogleShoppingAPI()

        gsf_log_tracker_id = False
        success_job = False
        for product in self:
            gs_account_id = product.gs_account_id
            instance = product.gs_instance_id
            google_product_id = product.google_product_id

            response_obj = GoogleShoppingAPIObj.delete_products_in_google_shopping_by_id_api(gs_account_id,
                                                                                             google_product_id)
            if response_obj.status_code in [401]:
                _logger.info("Call: Delete products, Reason: Expired Access Token, Status Code: 401")
                gs_account_id.get_gsf_refresh_tokens()
                response_obj = GoogleShoppingAPIObj.delete_products_in_google_shopping_by_id_api(gs_account_id,
                                                                                                 google_product_id)

            if response_obj.status_code == 204:
                vals = {
                    'exported_in_google_shopping': False,
                    'active_product_in_google_shopping': False
                }
                product.write(vals)
                if not success_job:
                    value = {
                        'gs_instance_id': instance.id,
                        'log_message': 'Delete Products from google shopping.',
                        'operation_sub_type': 'delete_product',
                        'operation_type': 'delete'
                    }
                    success_job = google_shopping_log_book.create(value)
                success_job_line_val = {
                    'record_reference': product.name,
                    'gsf_log_tracker_id': success_job.id,
                    'log_type': 'success',
                    'action_type': 'delete',
                    'operation_type': 'delete',
                    'message': 'Deleted successfully!!!',
                }
                google_shopping_log_book_line_obj.create(success_job_line_val)

            elif response_obj.status_code in [400, 404]:
                if not gsf_log_tracker_id:
                    value = {
                        'gs_instance_id': instance.id,
                        'log_message': 'Delete Products from google shopping.',
                        'operation_sub_type': 'delete_product',
                        'operation_type': 'delete',
                        'is_skip_process': True
                    }
                    gsf_log_tracker_id = google_shopping_log_book.create(value)
                log_line_vals = {
                    'record_reference': product.name,
                    'gsf_log_tracker_id': gsf_log_tracker_id.id,
                    'log_type': 'error',
                    'action_type': 'skip_line',
                    'operation_type': 'delete',
                    'message': response_obj.json(),
                }
                google_shopping_log_book_line_obj.create(log_line_vals)
            self._cr.commit()
        return True

    def import_google_shopping_products(self, instances, gs_account_id):
        """
            This method call to import google shopping products of the selected instances and account.
            
            @author: Grow Consultancy Services
            @return: True or Error
        """
        import_product_info_queue_gcs_obj = self.env['import.product.info.queue.gcs']
        import_product_info_queue_line_gcs_obj = self.env['import.product.info.queue.line.gcs']
        GoogleShoppingAPIObj = GoogleShoppingAPI()

        response_obj = GoogleShoppingAPIObj.import_google_shopping_products_api(gs_account_id)
        if response_obj.status_code in [401]:
            _logger.info("Call: Import all products, Reason: Expired Access Token, Status Code: 401")
            gs_account_id.get_gsf_refresh_tokens()
            response_obj = GoogleShoppingAPIObj.import_google_shopping_products_api(gs_account_id)

        instance_wise_counter_dict = {i: 200 for i in instances}
        instance_wise_queue_dict = {i: False for i in instances}
        import_product_info_queue = False
        import_product_info_queue_list = []
        if response_obj.status_code == 200:
            response = response_obj.json()
            products_dict = response.get('resources', [])
            for product_dict in products_dict:
                offer_id = product_dict.get('offerId')
                title = product_dict.get('title')
                target_country = product_dict.get('targetCountry')
                instance = instances.filtered(lambda x: x.country_id and x.country_id.code == target_country)
                if not instance or len(instance) > 1:
                    continue

                if instance_wise_counter_dict[instance] == 200:
                    import_product_info_queue = import_product_info_queue_gcs_obj.create({
                        'gs_instance_id': instance.id
                    })
                    instance_wise_queue_dict[instance] = import_product_info_queue
                    import_product_info_queue_list.append(import_product_info_queue.id)
                    message = "Product Queue Created %s" % import_product_info_queue.name
                    import_product_info_queue.generate_sendone_notification(message)
                    self._cr.commit()
                    instance_wise_counter_dict[instance] = 1
                import_product_info_queue_line_gcs_obj.create({
                    "product_offer_id": offer_id,
                    "name": title,
                    "synced_product_response": json.dumps(product_dict),
                    "import_product_info_queue_id": instance_wise_queue_dict[instance] and instance_wise_queue_dict[
                        instance].id or False,
                    "response_status_code": response_obj.status_code
                })
                instance_wise_counter_dict[instance] = instance_wise_counter_dict[instance] + 1
                self._cr.commit()
        return True

    def auto_process_import_product_info_queues(self):
        """
            This method call to import google shopping products of the selected instances and account.
            
            @author: Grow Consultancy Services
            @return: True or Error
        """
        import_product_info_queue_gcs_obj = self.env['import.product.info.queue.gcs']
        import_product_info_queue_ids = []
        query = """
            SELECT queue.id
            FROM import_product_info_queue_line_gcs AS queue_line
            INNER JOIN import_product_info_queue_gcs AS queue on queue_line.import_product_info_queue_id = queue.id
            WHERE queue_line.state='draft'
            ORDER BY queue_line.create_date ASC
        """
        self._cr.execute(query)
        import_product_info_queue_list = self._cr.fetchall()
        if not import_product_info_queue_list:
            return True

        for result in import_product_info_queue_list:
            if result[0] not in import_product_info_queue_ids:
                import_product_info_queue_ids.append(result[0])

        queues = import_product_info_queue_gcs_obj.browse(import_product_info_queue_ids)
        self.filter_and_process_import_product_info_queue_queue(queues)
        return True

    def filter_and_process_import_product_info_queue_queue(self, queues):
        """
        This method call to import google shopping products of the selected instances and account.
        
        @author: Grow Consultancy Services
        @return: True or Error
        """
        for queue in queues:
            import_product_info_queue_lines = \
                queue.import_product_info_queue_lines.filtered(lambda x: x.state == "draft")
            self.process_import_product_info_queue_queue(import_product_info_queue_lines)

    def process_import_product_info_queue_queue(self, import_product_info_queue_lines):
        """
        This method call to import google shopping products of the selected instances and account.
            
        @author: Grow Consultancy Services
        @return: True or Error
        """
        google_shopping_log_book = self.env['google.shopping.feed.log.tracker']
        google_shopping_log_book_line_obj = self.env['google.shopping.feed.log.line.tracker']
        google_shopping_product_variants_obj = self.env['google.shopping.product.variants']
        product_brand_gsf_obj = self.env['product.brand.gsf']
        odoo_product_product_obj = self.env['product.product']

        gsf_log_tracker_id = False
        for queue_line in import_product_info_queue_lines:
            gs_instance_id = queue_line.gs_instance_id
            queue_id = queue_line.import_product_info_queue_id
            product_dict = json.loads(queue_line.synced_product_response)
            response_status_code = queue_line.response_status_code
            offer_id = queue_line.product_offer_id

            if response_status_code == '200':
                google_product_id = product_dict.get('id')
                google_shopping_product_variant = google_shopping_product_variants_obj.search([
                    '&', ('gs_instance_id', '=', gs_instance_id.id),
                    '|', ('offer_id', '=', offer_id),
                    ('google_product_id', '=', google_product_id)
                ], limit=1)

                # If product found in Odoo Google Shopping Connector
                if google_shopping_product_variant:
                    vals = {
                        'exported_in_google_shopping': True,
                        'active_product_in_google_shopping': True if product_dict.get('channel') == 'online' else False,
                        'description': product_dict.get('description'),
                        'product_condition': product_dict.get('condition'),
                        'name': product_dict.get('title'),
                        'gtin': product_dict.get('gtin'),
                        'mpn': product_dict.get('mpn'),
                        'product_shop_link': product_dict.get('link'),
                        'channel': product_dict.get('channel'),
                    }
                    if product_dict.get('availability') == "in stock":
                        vals.update({'availability': 'in_stock'})
                    elif product_dict.get('availability') == "out of stock":
                        vals.update({'availability': 'out_of_stock'})
                    if product_dict.get('brand'):
                        brand_id = product_brand_gsf_obj.search([('name', '=ilike', product_dict.get('brand'))],
                                                                limit=1)
                        brand_id and vals.update({'brand': brand_id.id})
                    google_shopping_product_variant.write(vals)
                    queue_line.write({'state': 'done'})
                else:
                    # If product not found in Odoo Google Shopping Connector
                    # Check product available in Odoo base Product
                    odoo_product = odoo_product_product_obj.search([
                        ('default_code', '=', offer_id)
                    ], limit=1)
                    if odoo_product:
                        vals = {
                            'gs_instance_id': gs_instance_id.id,
                            'odoo_product_id': odoo_product.id,
                            'offer_id': odoo_product.default_code,
                            'google_product_id': product_dict.get('id'),
                            'exported_in_google_shopping': True,
                            'active_product_in_google_shopping': True if product_dict.get(
                                'channel') == 'online' else False,
                            'description': product_dict.get('description'),
                            'product_condition': product_dict.get('condition'),
                            'name': product_dict.get('title'),
                            'gtin': product_dict.get('gtin'),
                            'mpn': product_dict.get('mpn'),
                            'product_shop_link': product_dict.get('link'),
                            'channel': product_dict.get('channel'),
                        }
                        if product_dict.get('availability') == "in stock":
                            vals.update({'availability': 'in_stock'})
                        elif product_dict.get('availability') == "out of stock":
                            vals.update({'availability': 'out_of_stock'})
                        if product_dict.get('brand'):
                            brand_id = product_brand_gsf_obj.search([('name', '=ilike', product_dict.get('brand'))],
                                                                    limit=1)
                            brand_id and vals.update({'brand': brand_id.id})
                        google_shopping_product_variants_obj.create(vals)
                        queue_line.write({'state': 'done'})
                    else:
                        if not gsf_log_tracker_id:
                            value = {
                                'gs_instance_id': gs_instance_id.id,
                                'log_message': 'Not imported products due to not found in Odoo.',
                                'operation_sub_type': 'import_product',
                                'operation_type': 'import',
                                'is_skip_process': True
                            }
                            gsf_log_tracker_id = google_shopping_log_book.create(value)
                            queue_id.write({'log_tracker': gsf_log_tracker_id.id})
                        job_line_val = {
                            'record_reference': product_dict.get('offerId'),
                            'gsf_log_tracker_id': gsf_log_tracker_id.id,
                            'log_type': 'error',
                            'action_type': 'skip_line',
                            'operation_type': 'import',
                            'message': "Not found product in Odoo. Product Response: %s" % product_dict,
                            'import_product_info_queue_line_id': queue_line.id
                        }
                        google_shopping_log_book_line_obj.create(job_line_val)
                        queue_line.write({'state': 'failed'})
            self._cr.commit()
        return True

    def prepare_product_inventory_dict(self):
        instance = self.gs_instance_id
        google_shopping_account_id = self.gs_account_id
        vals = {
            'availability': "in stock" if self.availability == "in_stock" else "out of stock",
        }

        product_price = self.odoo_product_id.with_context({
            'pricelist': instance.pricelist.id,
            'quantity': 1
        }).price
        tax_price = self._calculate_product_tax_price(instance, product_price)
        vals['price'] = {
            "value": product_price and round(product_price + tax_price, 2) or 0.00,
            "currency": instance.pricelist.currency_id.name
        }

        offer_pricelist = instance.offer_pricelist
        if offer_pricelist:
            offer_line_price_rule = offer_pricelist.get_product_price_rule(product=self.odoo_product_id,
                                                                           quantity=1, partner=False)
            pricelist_rule_line = offer_line_price_rule and offer_pricelist.item_ids.filtered(lambda x:
                                                                                              x.id ==
                                                                                              offer_line_price_rule[
                                                                                                  1]) or False
            offer_price = offer_line_price_rule and \
                          round(offer_line_price_rule[0] + \
                                self._calculate_product_tax_price(instance, offer_line_price_rule[0]),
                                2) or product_price

            if pricelist_rule_line and pricelist_rule_line.date_start and pricelist_rule_line.date_end:
                offer_startdate = pricelist_rule_line.date_start.astimezone(pytz.utc)
                offer_enddate = pricelist_rule_line.date_end.astimezone(pytz.utc)
                current_date = datetime.datetime.now().astimezone(pytz.utc)

                if offer_startdate <= current_date <= offer_enddate:
                    final_offer_start_date = offer_startdate.strftime("%Y-%m-%dT%H:%MZ")
                    final_offer_end_date = offer_enddate.strftime("%Y-%m-%dT%H:%MZ")
                    sale_price_effective_date = "%s/%s" % (final_offer_start_date, final_offer_end_date)
                    vals.update({
                        'sale_price': {
                            "value": offer_price,
                            "currency": offer_pricelist.currency_id.name
                        },
                        'sale_price_effective_date': sale_price_effective_date
                    })
                else:
                    vals.update({
                        'sale_price': {
                            "value": offer_price,
                            "currency": offer_pricelist.currency_id.name
                        },
                        'sale_price_effective_date': ''
                    })

            else:
                vals.update({
                    'sale_price': {
                        "value": offer_price,
                        "currency": offer_pricelist.currency_id.name
                    },
                    'sale_price_effective_date': ''
                })

        if google_shopping_account_id.stock_field:
            product_stock = self.get_google_shopping_product_stock(self, google_shopping_account_id.warehouse_ids,
                                                                   google_shopping_account_id.stock_field.name)
        else:
            product_stock = self.get_google_shopping_product_stock(self,
                                                                   google_shopping_account_id.warehouse_ids,
                                                                   '')
        vals.update({'sellOnGoogleQuantity': round(product_stock, 2)})
        return vals

    def update_product_inventory_info(self):
        """
        This method used to create Update Product Inventory Info Queues.
        @author: Grow Consultancy Services
        @return: True or Error
        """
        update_product_inventory_info_queue_gcs_obj = self.env['update.product.inventory.info.queue.gcs']
        update_product_inventory_info_queue_line_gcs_obj = self.env['update.product.inventory.info.queue.line.gcs']
        instance_wise_counter_dict, instance_wise_queue_dict = self.prepare_instance_wise_counter_queue()
        queue_id = False
        queue_list = []
        for product in self:
            gs_instance_id = product.gs_instance_id
            if instance_wise_counter_dict[gs_instance_id] == 200:
                queue_id = update_product_inventory_info_queue_gcs_obj.create({
                    'gs_instance_id': gs_instance_id.id
                })
                instance_wise_queue_dict[gs_instance_id] = queue_id
                queue_list.append(queue_id.id)
                message = "Product Queue Created %s" % queue_id.name
                queue_id.generate_sendone_notification(message)
                self._cr.commit()
                instance_wise_counter_dict[gs_instance_id] = 1
            #
            product_dict = product.prepare_product_inventory_dict()
            update_product_inventory_info_queue_line_gcs_obj.create({
                "product_offer_id": product.offer_id,
                "name": product.name,
                "product_inventory_request_data": json.dumps(product_dict),
                "update_product_inventory_info_queue_id": queue_id and queue_id.id or False,
            })
            instance_wise_counter_dict[gs_instance_id] = instance_wise_counter_dict[gs_instance_id] + 1
            self._cr.commit()
        return True

    def auto_process_update_product_inventory_info_queues(self):
        """
        This method use to Update Product Inventory Info in Google Shopping.
        @author: Grow Consultancy Services
        @return: True or Error
        """
        update_product_inventory_info_queue_gcs_obj = self.env['update.product.inventory.info.queue.gcs']
        update_product_inventory_info_queue_ids = []
        query = """
            SELECT queue.id
            FROM update_product_inventory_info_queue_line_gcs AS queue_line
            INNER JOIN update_product_inventory_info_queue_gcs AS queue ON 
                queue_line.update_product_inventory_info_queue_id = queue.id
            WHERE queue_line.state='draft'
            ORDER BY queue_line.create_date ASC
        """
        self._cr.execute(query)
        query_result_list = self._cr.fetchall()
        if not query_result_list:
            return True

        for result in query_result_list:
            if result[0] not in update_product_inventory_info_queue_ids:
                update_product_inventory_info_queue_ids.append(result[0])

        queues = update_product_inventory_info_queue_gcs_obj.browse(update_product_inventory_info_queue_ids)
        self.filter_and_process_update_product_inventory_info_queue(queues)
        return True

    def filter_and_process_update_product_inventory_info_queue(self, queues):
        """
        @author: Grow Consultancy Services
        @return: True or Error
        """
        for queue in queues:
            update_product_inventory_info_queue_lines = \
                queue.update_product_inventory_info_queue_lines.filtered(lambda x: x.state == "draft")
            self.process_update_product_inventory_info_queue(update_product_inventory_info_queue_lines)

    def process_update_product_inventory_info_queue(self, update_product_inventory_info_queue_lines):
        google_shopping_log_book = self.env['google.shopping.feed.log.tracker']
        google_shopping_log_book_line_obj = self.env['google.shopping.feed.log.line.tracker']
        GoogleShoppingAPIObj = GoogleShoppingAPI()

        gsf_log_tracker_id = False
        for queue_line in update_product_inventory_info_queue_lines:
            gs_account_id = queue_line.gs_account_id
            gs_instance_id = queue_line.gs_instance_id
            product_dict = json.loads(queue_line.product_inventory_request_data)
            gsf_product = self.search([('offer_id', '=', queue_line.product_offer_id),
                                       ('gs_account_id', '=', gs_account_id.id),
                                       ('gs_instance_id', '=', gs_instance_id.id)], limit=1)
            google_product_id = gsf_product.google_product_id
            queue_id = queue_line.update_product_inventory_info_queue_id

            response_obj = GoogleShoppingAPIObj.update_product_inventory_info_api(gs_account_id, product_dict,
                                                                                  google_product_id)
            if response_obj.status_code in [401]:
                _logger.info("Call: Update Product Inventory Info, Reason: Expired Access Token, Status Code: 401")
                gs_account_id.get_gsf_refresh_tokens()
                response_obj = GoogleShoppingAPIObj.update_product_inventory_info_api(gs_account_id, product_dict,
                                                                                      google_product_id)

            if response_obj.status_code == 200:
                queue_line.write({'state': 'done'})
                continue
            elif response_obj.status_code in [400, 404]:
                if not gsf_log_tracker_id:
                    value = {
                        'gs_instance_id': gs_instance_id.id,
                        'log_message': 'Update Product Inventory Info to google shopping.',
                        'operation_sub_type': 'update_product',
                        'operation_type': 'update',
                        'is_skip_process': True
                    }
                    gsf_log_tracker_id = google_shopping_log_book.create(value)
                    queue_id.write({'log_tracker': gsf_log_tracker_id.id})
                job_line_val = {
                    'record_reference': gsf_product.name,
                    'gsf_log_tracker_id': gsf_log_tracker_id.id,
                    'log_type': 'error',
                    'action_type': 'skip_line',
                    'operation_type': 'update',
                    'message': response_obj.text,
                    'update_product_inventory_info_queue_line_id': queue_line.id
                }
                google_shopping_log_book_line_obj.create(job_line_val)
                queue_line.write({'state': 'failed'})
            self._cr.commit()
        return True

    def get_product_status_from_google_shopping(self):
        """
        This method used to get product status queues.
        
        @author: Grow Consultancy Services
        @return: True or Error
        """
        get_product_status_queue_gcs_obj = self.env['get.product.status.queue.gcs']
        get_product_status_queue_lines_gcs_obj = self.env['get.product.status.queue.lines.gcs']
        GoogleShoppingAPIObj = GoogleShoppingAPI()

        instance_wise_counter_dict, instance_wise_queue_dict = self.prepare_instance_wise_counter_queue()
        get_product_status_queue = False
        get_product_status_queue_list = []
        for product in self:
            gs_instance_id = product.gs_instance_id
            gs_account_id = product.gs_account_id
            if instance_wise_counter_dict[gs_instance_id] == 200:
                get_product_status_queue = get_product_status_queue_gcs_obj.create({
                    'gs_instance_id': gs_instance_id.id
                })
                instance_wise_queue_dict[gs_instance_id] = get_product_status_queue
                get_product_status_queue_list.append(get_product_status_queue.id)
                message = "Product Queue Created %s" % get_product_status_queue.name
                get_product_status_queue.generate_sendone_notification(message)
                self._cr.commit()
                instance_wise_counter_dict[gs_instance_id] = 1

            response_obj = GoogleShoppingAPIObj.get_product_status_from_google_shopping_api(gs_account_id,
                                                                                            product.google_product_id)
            if response_obj.status_code in [401]:
                _logger.info(
                    "Call:Get Product Status from Google Shopping, Reason: Expired Access Token, Status Code: 401")
                gs_account_id.get_gsf_refresh_tokens()
                response_obj = GoogleShoppingAPIObj.get_product_status_from_google_shopping_api(
                    gs_account_id,
                    product.google_product_id)

            product_dict = response_obj.json()
            get_product_status_queue_lines_gcs_obj.create({
                "product_offer_id": product.offer_id,
                "name": product.name,
                "synced_product_response": json.dumps(product_dict),
                "get_product_status_queue_id": get_product_status_queue and get_product_status_queue.id or False,
                "response_status_code": response_obj.status_code
            })
            instance_wise_counter_dict[gs_instance_id] = instance_wise_counter_dict[gs_instance_id] + 1
            self._cr.commit()
        return True

    def auto_process_get_product_status_queues(self):
        """
        This method used to get product status queues.
        
        @author: Grow Consultancy Services
        @return: True or Error
        """
        get_product_status_queue_gcs_obj = self.env['get.product.status.queue.gcs']
        get_product_status_queue_ids = []
        query = """
            SELECT queue.id
            FROM get_product_status_queue_lines_gcs AS queue_line
            INNER JOIN get_product_status_queue_gcs AS queue on queue_line.get_product_status_queue_id = queue.id
            WHERE queue_line.state='draft'
            ORDER BY queue_line.create_date ASC
        """
        self._cr.execute(query)
        get_product_status_queue_list = self._cr.fetchall()
        if not get_product_status_queue_list:
            return True

        for result in get_product_status_queue_list:
            if result[0] not in get_product_status_queue_ids:
                get_product_status_queue_ids.append(result[0])

        queues = get_product_status_queue_gcs_obj.browse(get_product_status_queue_ids)
        self.filter_and_process_get_product_status_queue(queues)
        return True

    def filter_and_process_get_product_status_queue(self, queues):
        """
        This method used to get product status queues.
        
        @author: Grow Consultancy Services
        @return: True or Error
        """
        for queue in queues:
            get_product_status_queue_lines = \
                queue.get_product_status_queue_lines.filtered(lambda x: x.state == "draft")
            self.process_get_product_status_queue(get_product_status_queue_lines)

    def process_get_product_status_queue(self, get_product_status_queue_lines):
        """
        This method used to get product status queues.
        
        @author: Grow Consultancy Services
        @return: True or Error
        """
        google_shopping_log_book = self.env['google.shopping.feed.log.tracker']
        google_shopping_log_book_line_obj = self.env['google.shopping.feed.log.line.tracker']
        gsf_log_tracker_id = False
        for queue_line in get_product_status_queue_lines:
            gs_account_id = queue_line.gs_account_id
            gs_instance_id = queue_line.gs_instance_id
            queue_id = queue_line.get_product_status_queue_id
            product_dict = json.loads(queue_line.synced_product_response)
            response_status_code = queue_line.response_status_code
            product = self.search([('offer_id', '=', queue_line.product_offer_id),
                                   ('gs_account_id', '=', gs_account_id.id),
                                   ('gs_instance_id', '=', gs_instance_id.id)], limit=1)
            if response_status_code == '200':
                destination_statuses = product_dict.get('destinationStatuses', [])
                product_expiration_date = product_dict.get('googleExpirationDate', '')
                src_date = product_expiration_date[:19]
                src_date = time.strptime(src_date, "%Y-%m-%dT%H:%M:%S")
                product_expiration_date = time.strftime("%Y-%m-%d %H:%M:%S", src_date)
                product_status = destination_statuses and destination_statuses[0].get('status', '')
                product.write({
                    'product_status': product_status,
                    'product_expiration_date': product_expiration_date
                })
                queue_line.write({'state': 'done'})
            elif response_status_code in ['400', '404']:
                if not gsf_log_tracker_id:
                    value = {
                        'gs_instance_id': gs_instance_id.id,
                        'log_message': 'Get products status from Google Shopping.',
                        'operation_sub_type': 'import_product',
                        'operation_type': 'import',
                        'is_skip_process': True
                    }
                    gsf_log_tracker_id = google_shopping_log_book.create(value)
                    queue_id.write({'log_tracker': gsf_log_tracker_id.id})
                job_line_val = {
                    'record_reference': product.name,
                    'gsf_log_tracker_id': gsf_log_tracker_id.id,
                    'log_type': 'error',
                    'action_type': 'skip_line',
                    'operation_type': 'import',
                    'message': product_dict,
                    'get_product_status_queue_line_id': queue_line.id
                }
                google_shopping_log_book_line_obj.create(job_line_val)
                queue_line.write({'state': 'failed'})
            self._cr.commit()
        return True

    def prepare_instance_wise_counter_queue(self):
        google_shopping_feed_instance_obj = self.env['google.shopping.feed.instance']
        gs_instance_ids = google_shopping_feed_instance_obj.search([('state', '=', 'confirmed')])
        instance_wise_counter_dict = {i: 200 for i in gs_instance_ids}
        instance_wise_queue_dict = {i: False for i in gs_instance_ids}
        return instance_wise_counter_dict, instance_wise_queue_dict
