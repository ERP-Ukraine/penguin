# -*- coding: utf-8 -*-
{
    'name': 'Penguin Website',
    'author': 'ERP Ukraine',
    'website': 'https://erp.co.ua',
    'support': 'support@erp.co.ua',
    'license': 'LGPL-3',
    'category': 'Website/Website',
    'version': '1.3',
    'sequence': 7,
    'depends': ['website'],
    'data': ['views/website_templates.xml'],
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
