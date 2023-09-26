# -*- coding: utf-8 -*-
{
    'name': 'Penguin Website',
    'author': 'ERP Ukraine',
    'website': 'https://erp.co.ua',
    'support': 'support@erp.co.ua',
    'license': 'LGPL-3',
    'category': 'Website/Website',
    'version': '2.1',
    'sequence': 7,
    'depends': ['website'],
    'data': [
        'views/website_templates.xml',
        'views/aboutus.xml',
        'views/accessoires.xml',
        'views/ambassador.xml',
        'views/care.xml',
        'views/customerservice.xml',
        'views/fleece.xml',
        'views/homepage.xml',
        'views/insulation.xml',
        'views/merino.xml',
        'views/movie.xml',
        'views/shell.xml',
        'views/philosophy.xml',
        'views/stores.xml',
        'views/toursandevents.xml',
        'data/website_data.xml',
    ],
    'assets': {
        'web._assets_frontend_helpers': [
            '/website_penguin/static/src/scss/bootstrap_variables.scss',
        ],
        'web.assets_frontend': [
            '/website_penguin/static/src/scss/website.scss'
        ],
    },
    'installable': True,
    'auto_install': True,
    'application': False,
}
