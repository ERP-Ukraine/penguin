{
    'name': 'Penguin Sales',
    'version': '1.2',
    'category': 'Sales/Sales',
    'summary': 'Sales internal machinery',
    'depends': ['sale', 'product_penguin'],
    'data': [
        'data/mail_data.xml',

        'report/sale_report_templates.xml',

        'views/sale_views.xml',
        'views/variant_templates.xml',
    ],
    'installable': True,
    'auto_install': True
}
