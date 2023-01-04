# -*- coding: utf-8 -*-
{
    'name': 'Inventory Penguin',
    'summary': 'Manage your stock and logistics activities',
    'author': 'ERP Ukraine',
    'website': 'https://erp.co.ua',
    'support': 'support@erp.co.ua',
    'license': 'LGPL-3',
    'category': 'Operations/Inventory',
    'version': '1.5',
    'depends': ['stock'],
    'data': [
        'report/report_deliveryslip.xml',
        'report/report_stockpicking_operations.xml',
    ],
    'installable': True,
    'auto_install': True,
    'application': False,
}
