# -*- coding: utf-8 -*-
{
    'name': 'Sale Stock Penguin',
    'summary': 'Sale and Stock connection module for Penguin',
    'author': 'ERP Ukraine',
    'website': 'https://erp.co.ua',
    'support': 'support@erp.co.ua',
    'license': 'LGPL-3',
    'category': 'Operations/Inventory',
    'version': '1.0',
    'depends': [
        'stock_penguin',
        'sale_stock'
    ],
    'data': [
        'views/stock_move_line_views.xml'
    ],
    'installable': False,
    'auto_install': True,
    'application': False,
}
