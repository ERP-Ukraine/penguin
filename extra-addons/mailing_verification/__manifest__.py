# -*- coding: utf-8 -*-
{
    'name': 'Mailing Verification',
    'version': '1.0',
    'summary': 'Mailing verification',
    'category': 'Marketing/Email Marketing',
    'author': 'ERP Ukraine',
    'website': 'https://erp.co.ua',
    'support': 'support@erp.co.ua',
    'license': 'AGPL-3',
    'depends': [
        'mass_mailing_res_partner_link',
        'website_mass_mailing',
        'mass_mailing_autocreate',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_cron_data.xml',
        'data/verification_templates.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
