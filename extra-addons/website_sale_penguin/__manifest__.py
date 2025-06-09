# -*- coding: utf-8 -*-
{
    'name': 'Penguin eCommerce',
    'summary': 'eCommerce customizations for Penguin',
    'author': 'ERP Ukraine',
    'website': 'https://erp.co.ua',
    'support': 'support@erp.co.ua',
    'license': 'LGPL-3',
    'category': 'Website/Website',
    'version': '2.9.1',
    'depends': ['website_penguin', 'website_sale'],
    'data': [
        'report/sale_report_templates.xml',
        'views/product_views.xml',
        'views/sale_views.xml',
        'views/templates.xml',
        'views/res_config_settings_views.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            '/website_sale_penguin/static/src/scss/website_sale.scss',
        ],
    },
    'auto_install': True,
    'application': True,
    'installable': False,
}
