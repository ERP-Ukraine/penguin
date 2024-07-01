# -*- coding: utf-8 -*-
{
    'name': 'Autoset Industry Field',
    'version': '2.0',
    'summary': 'Autoset industry field for new users',
    'category': 'Hidden',
    'author': 'ERP Ukraine',
    'website': 'https://erp.co.ua',
    'support': 'support@erp.co.ua',
    'license': 'LGPL-3',
    'depends': [
        'base_penguin',
        'product',
        'contacts'
    ],
    'data': [],
    'installable': False,
    'auto_install': False,
    'application': False,
    'post_init_hook': 'set_default_industry_field',
}
