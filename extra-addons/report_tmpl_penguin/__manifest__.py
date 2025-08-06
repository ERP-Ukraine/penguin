# -*- coding: utf-8 -*-
{
    'name': 'Penguin Report Template',
    'summary': 'Custom report header and footer for some pdf docs.',
    'author': 'ERP Ukraine',
    'website': 'https://erp.co.ua',
    'support': 'support@erp.co.ua',
    'license': 'LGPL-3',
    'category': 'Hidden',
    'version': '3.2',
    'description': """
Penguin Report Templates
=========================
This module adds warehouse address to account, sale and other reports
    """,
    'depends': [
        'l10n_ch',
        'sale_stock',
        'purchase_stock',
        'sale_purchase',
        'web',
    ],
    'data': [
        'data/data.xml',
        'report/reports.xml',
        'report/sale_order_reports.xml',
        'report/account_move_reports.xml',
        'report/stock_picking_reports.xml',
        'report/purchase_order_reports.xml',
        'views/res_company_views.xml',
        'views/stock_warehouse_views.xml',
        'views/sale_order_templates.xml',
    ],
    'assets': {
        'web.report_assets_common': [
            '/report_tmpl_penguin/static/src/scss/report_tmpl_penguin.scss',
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': False,
}
