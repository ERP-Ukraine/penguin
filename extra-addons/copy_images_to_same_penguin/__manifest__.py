# -*- coding: utf-8 -*-
{
    'name': 'Copy images to same, Penguin',
    'author': 'ERP Ukraine',
    'website': 'https://erp.co.ua',
    'support': 'support@erp.co.ua',
    'license': 'LGPL-3',
    'category': 'Other',
    'version': '1.1',
    'depends': [
        'product',
        'stock',
        'website_sale',
    ],
    'data': [
        'security/ir.model.access.csv',
        'wizard/product_product_same_images.xml',
        'views/product_product_views.xml',
    ],
    'auto_install': False,
    'installable': True,
    'application': False,
}
