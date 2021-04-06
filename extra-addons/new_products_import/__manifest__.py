# -*- coding: utf-8 -*-
{
    'name': 'New Products Import',
    'summary': 'Import new products with .xls files',
    'author': 'ERP Ukraine',
    'website': 'https://erp.co.ua',
    'support': 'support@erp.co.ua',
    'license': 'LGPL-3',
    'category': 'Sales/Sales',
    'version': '1.0',
    'description': """
New Products Import
===================
This module add wizard for importing new products  
    """,
    'depends': [
        'base_import',
        'product_penguin',
        'purchase',
        'stock',
    ],
    'data': [
        'wizard/new_product_import.xml'
    ],
    'auto_install': False,
    'installable': True,
    'application': False,
}
