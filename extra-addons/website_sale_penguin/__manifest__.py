# -*- coding: utf-8 -*-
{
    'name': 'Penguin eCommerce',
    'summary': 'eCommerce customizations for Penguin',
    'author': 'ERP Ukraine',
    'website': 'https://erp.co.ua',
    'support': 'support@erp.co.ua',
    'license': 'LGPL-3',
    'category': 'Website/Website',
    'version': '3.3',
    'depends': [
        'account',
        'sale',
        'website_penguin',
        'website_sale',
        ],
    'data': [
        'report/sale_report_templates.xml',
        'report/report_invoice.xml',
        'views/product_views.xml',
        'views/sale_views.xml',
        'views/templates.xml',
        'views/res_config_settings_views.xml',
        'views/account_move_views.xml',
    ],
    'auto_install': True,
    'application': True,
    'installable': True,
}
