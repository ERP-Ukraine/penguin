{
    'name': 'Penguin Products & Pricelists',
    'version': '1.2',
    'category': 'Sales/Sales',
    'depends': ['product'],
    'data': [
        'security/ir.model.access.csv',

        'data/product_data.xml',

        'views/product_attribute_views.xml',
        'views/product_views.xml',
    ],
    'installable': False,
    'auto_install': True,
    'license': 'LGPL-3',
}
