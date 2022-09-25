# -*- coding: utf-8 -*-
{
    'name': 'Order Import form Arnold Sports',
    'summary': 'Import orders from attachment sent to email',
    'author': 'ERP Ukraine LLC',
    'website': 'https://erp.co.ua',
    'support': 'support@erp.co.ua',
    'license': 'LGPL-3',
    'category': 'Sales/Sales',
    'version': '1.0',
    'depends': [
        'sale',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/mail_alias_data.xml',
        'data/ir_cron.xml',
        'views/res_config_settings_views.xml',
        'views/sale_order_arnold_views.xml',
    ],
    'auto_install': False,
    'installable': True,
    'application': False,
}
