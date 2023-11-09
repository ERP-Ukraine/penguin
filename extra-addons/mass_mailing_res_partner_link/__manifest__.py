# -*- coding: utf-8 -*-
{
    'name': 'Email Marketing + Contacts',
    'summary': 'Email Marketing and Contacts Connector',
    'description': "",
    'version': '1.0',
    'author': 'ERP Ukraine',
    'website': 'https://erp.co.ua',
    'support': 'support@erp.co.ua',
    'category': 'Marketing',
    'depends': ['base', 'mass_mailing'],
    'data': [
        'data/ir_cron_data.xml',
        'views/mailing_contact_views.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': False,
}
