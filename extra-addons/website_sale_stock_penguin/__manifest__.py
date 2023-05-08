# -*- coding: utf-8 -*-
{
    'name': 'Penguin Product Availability',
    'summary': 'Manage product inventory & availability',
    'author': 'ERP Ukraine',
    'website': 'https://erp.co.ua',
    'support': 'support@erp.co.ua',
    'license': 'LGPL-3',
    'category': 'Website/Website',
    'version': '1.5',
    'depends': [
        'sale_stock_penguin',
        'website_sale_penguin',
        'website_sale_stock_multi_warehouse',
    ],
    'data': [
        'report/report_deliveryslip.xml',
        'views/product_views.xml',
        'views/stock_warehouse_views.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'website_sale_stock_penguin/static/src/js/variant_mixin.js',
            'website_sale_stock_penguin/static/src/scss/website_sale_stock_penguin.scss',
        ],
    },
    'auto_install': True,
    'installable': True,
    'post_init_hook': 'set_inventory_availability_on_product_templates'
}
