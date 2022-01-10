# -*- coding: utf-8 -*-
{
    'name': 'Penguin Sales',
    'version': '2.2',
    'category': 'Sales/Sales',
    'summary': 'Sales internal machinery',
    'installable': True,
    'auto_install': True,
    'depends': [
        'product_penguin',
        'sale',
        'sale_enterprise',
        'stock',
    ],

    'data': [
        'data/mail_data.xml',
        'report/sale_report_templates.xml',
        'views/res_partner_views.xml',
        'views/res_users_view.xml',
        'views/sale_order_templates.xml',
        'views/sale_views.xml',
        'views/variant_templates.xml',
    ]
}
