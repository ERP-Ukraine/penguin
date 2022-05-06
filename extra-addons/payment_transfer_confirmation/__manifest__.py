# -*- coding: utf-8 -*-
{
    'name': 'Order Confirmation for Wire Transfer',
    'category': 'Accounting/Payment',
    'version': '1.0',
    'description': "Auto confirm order on payment confiramtion.",
    'author': 'ERP Ukraine',
    'website': 'https://erp.co.ua',
    'support': 'support@erp.co.ua',
    'license': 'LGPL-3',
    'depends': [
        'payment_transfer',
        'sale'
    ],
    'data': [
        'data/payment_data.xml',
        'views/payment_acquirer_views.xml',
    ],
    'auto_install': False,
    'installable': True,
    'application': False,
    'post_init_hook': 'wire_transfer_enable_authorization',
}
