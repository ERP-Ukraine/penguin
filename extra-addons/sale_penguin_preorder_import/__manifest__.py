# -*- coding: utf-8 -*-
{
    'name': 'Penguin Sales: pre-Order Import',
    'summary': 'Import preorder from xls template',
    'author': 'ERP Ukraine',
    'website': 'https://erp.co.ua',
    'support': 'support@erp.co.ua',
    'license': 'LGPL-3',
    'category': 'Sales/Sales',
    'version': '1.2',
    'depends': [
        'base_import',
        'sale_penguin',
    ],
    'data': [
        'security/ir.model.access.csv',
        'wizard/preorder_import.xml',
    ],
    'auto_install': True,
    'installable': True,
    'application': False,
}
