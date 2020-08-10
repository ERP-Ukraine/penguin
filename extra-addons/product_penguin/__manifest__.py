{
    'name': 'Penguin Products & Pricelists',
    'version': '13.0.1.0',
    'category': 'Sales/Sales',
    'depends': ['product'],
    'data': [
        'security/ir.model.access.csv',

        'data/product_data.xml',

        'views/product_views.xml'
    ],
    'installable': True,
    'auto_install': True,
}
