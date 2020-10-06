{
    'name': 'Copy images to same, Penguin',

    'version': '1.0',
    'category': 'Other',
    'author': 'ERP Ukraine',
    'website': 'https://erp.co.ua',
    'support': 'support@erp.co.ua',
    'license': 'OPL-1',
    'auto_install': False,
    'installable': True,
    'application': True,

    'demo': [],

    'depends': [
        'product',
        'stock',
        'website_sale',
    ],

    'data': [
        'wizards/product_product_same_images.xml',
        'views/product_product_views.xml',
    ],
}
