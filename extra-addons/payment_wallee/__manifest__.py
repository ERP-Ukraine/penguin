# -*- coding: utf-8 -*-
#################################################################################
# Author      : PIT Solutions AG. (<https://www.pitsolutions.com/>)
# Copyright(c): 2019 - Present PIT Solutions AG.
# License URL : https://www.webshopextension.com/en/licence-agreement/
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <https://www.webshopextension.com/en/licence-agreement/>
#################################################################################

{
    'name': 'Wallee Payment Acquirer Plugin',
    'category': 'Payment Gateway',
    'summary': '''Payment Acquirer: Wallee Implementation
        Payment Acquirer: Wallee.com
        More infos on integrated payment gateways,https://app-wallee.com
    ''',
    'version': '18.0.3.0.0',
    'description': """Wallee Payment Acquirer""",
    'currency': 'EUR',
    'price': 173,
    'license': 'Other proprietary',
    'author': 'PIT Solutions AG',
    'website': 'https://www.pitsolutions.com/',
    'depends': ['website_payment', 'payment','pits_payment_provider_base'],
    'external_dependencies': {
        'python': ['cairosvg', 'wallee']
    },
    'data': [
        'security/ir.model.access.csv',
        'data/ir_cron_data.xml',
        'data/email_templates.xml',
        'wizard/account_payment_register.xml',
        'wizard/warning_message_wiz_views.xml',
        'views/wallee_payment_method_views.xml',
        'views/payment_acquirer_views.xml',
        'views/account_move_views.xml',
        'views/payment_transaction_views.xml',
        'views/wallee_templates.xml',
        'data/payment_acquirer_data.xml',
    ],
    'images': [
        'static/description/banner.png',
    ],
    'installable': True,
    'post_init_hook': 'post_init_hook',
    'uninstall_hook': 'uninstall_hook',
    'assets': {
        'web.assets_frontend': [
            'payment_wallee/static/src/css/payment_form.css',
            'payment_wallee/static/src/js/**/*',
            'payment_wallee/static/src/xml/**/*',
        ],
    }
}
