# -*- coding: utf-8 -*-
{
    'name': 'Bloopark Detail page',
    'version': '17.0',
    'author': 'Bloopark systems GmbH & Co. KG',
    'website': 'https://bloopark.de',
    'support': 'support@/bloopark.de',
    'license': 'LGPL-3',
    'category': 'Website/Website',
    'sequence': 7,
    'depends': ['website_sale_penguin', 'theme_prime', 'product_penguin'],
    'data': ['views/layout.xml'],
    'images': ['static/description/icon.png'],
    'assets': {
        'web.assets_frontend': [
            'website_bloopark_detail/static/src/scss/style.scss',
            'website_bloopark_detail/static/src/js/script.js',
        ],
    },
    'installable': True,
    'auto_install': True,
}
