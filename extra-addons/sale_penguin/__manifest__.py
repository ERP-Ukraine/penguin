{
    'name': 'Penguin Sales',
    'version': '1.3',
    'category': 'Sales/Sales',
    'summary': 'Sales internal machinery',
    'installable': True,
    'auto_install': True,

    'depends': [
        'sale',
        'product_penguin',
    ],

    'data': [
        'data/mail_data.xml',
        'report/sale_report_templates.xml',
        'views/sale_views.xml',
        'views/variant_templates.xml',
        'views/sale_order_templates.xml',
    ]
}
