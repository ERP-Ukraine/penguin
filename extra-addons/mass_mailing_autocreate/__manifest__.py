# -*- coding: utf-8 -*-
{
    'name': 'Mass Mailing Autocreate',
    'version': '1.0',
    'summary': 'Mass mailing autocreate',
    'category': 'Marketing/Email Marketing',
    'author': 'ERP Ukraine',
    'website': 'https://erp.co.ua',
    'support': 'support@erp.co.ua',
    'license': 'AGPL-3',
    'depends': [
        'contacts',
        'mass_mailing',
    ],
    'data': [
        'views/res_config_settings_views.xml',
    ],
    'installable': False,
    'auto_install': False,
    'application': False,
    'post_init_hook': 'add_contacts_to_mailing_list',
}
