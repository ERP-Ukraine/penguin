# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
#################################################################################
# Author      : Grow Consultancy Services (<https://www.growconsultancyservices.com/>)
# Copyright(c): 2021-Present Grow Consultancy Services
# All Rights Reserved.
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
#################################################################################
{
    # Application Information
    'name': 'Odoo Google Merchant/Shopping Connector',
    'version': '15.0.3.1.0',
    'category': 'Sales',
    'license': 'OPL-1',

    'summary': """
Google Shopping is expanding worldwide and along with Google Shopping, Your business the potential to grow
globally. If you use Odoo to manage your backend operations along with having a Google Shopping Store,
Odoo Google Shopping Integration becomes absolutely vital for you. Odoo Google Shopping Connector will help
you integrate and manage your Google Shopping Store in Odoo. Perform various operations like Export products,
Updating products information, Updating inventory, Deleting products, and Much more.

Odoo Google Merchant Connector, Odoo Google Merchant Center, Odoo Google Shopping Connector,
Odoo Google Shopping Feed, Odoo Google Feed, Odoo Google Product Feed

GCS also provides various types of solutions, such as Odoo WooCommerce Integration, Odoo Shopify Integration,
Odoo Direct Print, Odoo Amazon Connector, Odoo eBay Odoo Integration, Odoo Amazon Integration,
Odoo Magento Integration, Dropshipper EDI Integration, Dropshipping EDI Integration, Shipping Integrations,
Odoo Shipstation Integration, Odoo GLS Integration, DPD Integration, FedEx Integration, Aramex Integration,
Soundcloud Integration, Website RMA, DHL Shipping, Bol.com Integration, Google Shopping/Merchant Integration,
Marketplace Integration, Payment Gateway Integration, Dashboard Ninja, Odoo Direct Print Pro, Odoo Printnode,
Dashboard Solution, Cloud Storage Solution, MailChimp Connector, PrestaShop Connector, Inventory Report,
Power BI, Odoo Saas, Quickbook Connector, Multi Vendor Management, BigCommerce Odoo Connector,
Rest API, Email Template, Website Theme, Various Website Solutions, etc.
    """,
    'description': """
Google Shopping is expanding worldwide and along with Google Shopping, Your business the potential to grow
globally. If you use Odoo to manage your backend operations along with having a Google Shopping Store,
Odoo Google Shopping Integration becomes absolutely vital for you. Odoo Google Shopping Connector will help
you integrate and manage your Google Shopping Store in Odoo. Perform various operations like Export products,
Updating products information, Updating inventory, Deleting products, and Much more.

Odoo Google Merchant Connector, Odoo Google Merchant Center, Odoo Google Shopping Connector,
Odoo Google Shopping Feed, Odoo Google Feed, Odoo Google Product Feed

GCS also provides various types of solutions, such as Odoo WooCommerce Integration, Odoo Shopify Integration,
Odoo Direct Print, Odoo Amazon Connector, Odoo eBay Odoo Integration, Odoo Amazon Integration,
Odoo Magento Integration, Dropshipper EDI Integration, Dropshipping EDI Integration, Shipping Integrations,
Odoo Shipstation Integration, Odoo GLS Integration, DPD Integration, FedEx Integration, Aramex Integration,
Soundcloud Integration, Website RMA, DHL Shipping, Bol.com Integration, Google Shopping/Merchant Integration,
Marketplace Integration, Payment Gateway Integration, Dashboard Ninja, Odoo Direct Print Pro, Odoo Printnode,
Dashboard Solution, Cloud Storage Solution, MailChimp Connector, PrestaShop Connector, Inventory Report,
Power BI, Odoo Saas, Quickbook Connector, Multi Vendor Management, BigCommerce Odoo Connector,
Rest API, Email Template, Website Theme, Various Website Solutions, etc.
    """,

    # Author Information
    'author': 'Grow Consultancy Services',
    'maintainer': 'Grow Consultancy Services',
    'website': 'http://www.growconsultancyservices.com',

    # Application Price Information
    'price': 99,
    'currency': 'EUR',

    # Dependencies
    'depends': ['website_sale', 'sale_management', 'delivery', 'base_setup', 'google_products_category_gcs'],

    # Views
    'data': [
        'security/res_groups.xml',
        'security/ir.model.access.csv',
        'view/menus.xml',
        'view/gsf_account_view.xml',
        'view/gsf_instance_view.xml',
        'view/gsf_product_view.xml',
        'view/product_view.xml',
        'wizard/gsf_import_export_operations_wizard_view.xml',
        'view/gsf_log_book_view.xml',
        'data/ir_sequence.xml',
        'view/gsf_product_images_view.xml',
        'wizard/gsf_global_operations_view.xml',
        'wizard/res_config_settings.xml',
        'view/gsf_product_brand.xml',
        'view/product_image.xml',
        'wizard/gsf_crons_setting_view.xml',
        'data/ir_cron.xml',
        'wizard/queue_process_wizard_view.xml',
        'view/update_product_data_queue_views.xml',
        'view/update_product_inventory_info_queue_views.xml',
        'view/get_product_status_queue_views.xml',
        'view/import_product_info_queue_views.xml',
        'wizard/product_image_url_update_wizard_views.xml',
        # 'view/'
        # wizard/
    ],

    # Application Main Image
    'images': ['static/description/app_profile_image.jpg'],

    # Technical
    'installable': False,
    'application': True,
    'auto_install': False,
    'active': False,
}
