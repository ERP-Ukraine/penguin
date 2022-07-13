# -*- coding: utf-8 -*-
# Part of PIT Solutions AG. See LICENSE file for full copyright and licensing details.

{
    'name': 'Wallee Payment Acquirer Plugin From PIT Solutions',
    'category': 'Payment Gateway',
    'summary': '''Payment Acquirer: Wallee Implementation
        Payment Acquirer: Wallee.com
        More infos on integrated payment gateways,https://app-wallee.com
    ''',
    'version': '15.0.1.1',
    'description': """Wallee Payment Acquirer""",
    'currency': 'EUR',
    'price': 150,
    'license': 'OPL-1',
    'author': 'PIT Solutions AG',
    'website': 'http://www.pitsolutions.ch/en/',
    'depends': ['account_payment'],
    'data': [
        'security/ir.model.access.csv',
        'views/payment_acquirer_log.xml',
        'views/wallee_payment_method_views.xml',
        'views/payment_views.xml',
        'views/wallee_templates.xml',
        'data/payment_acquirer_data.xml',
        'data/ir_cron_data.xml',
    ],
    'images': ['static/description/banner.png',
    ],
    'installable': True,
    'uninstall_hook': 'uninstall_hook',
    'assets': {
            'web.assets_frontend': [
                'payment_wallee/static/src/scss/payment_form.scss',
                'payment_wallee/static/src/css/payment_form.css',
                'payment_wallee/static/src/js/payment_form.js',
                'payment_wallee/static/src/js/wallee_interface.js',
                'payment_wallee/static/src/js/payment_processing.js',
            ],
            'web.assets_qweb': [
                'payment_wallee/static/src/xml/**/*',
            ],
    }
}

