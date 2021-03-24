# -*- coding: utf-8 -*-
{
    'name': 'Penguin Coupons',
    'version': '1.1',
    'category': 'Sales/Sales',
    'summary': 'Sales Coupon Customs Design',
    'installable': True,
    'auto_install': True,
    'depends': [
        'sale_coupon',
    ],

    'data': [
        'views/assets.xml',
        'report/sale_coupon_report_templates.xml',
        'views/sale_coupon_program_views.xml',
        'views/sale_coupon_views.xml'
    ]
}
