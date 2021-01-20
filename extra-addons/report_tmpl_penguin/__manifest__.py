{
    'name': 'Penguin Report Template',
    'version': '2.1',
    'summary': 'Custom report header and footer for some pdf docs.',
    'installable': True,
    'auto_install': False,

    'description': """
Penguin Report Templates
=========================
This module adds warehouse address to account, sale and other reports
    """,
    'depends': [
        'account',
        'base',
        'l10n_ch',
        'sale',
        'sale_stock',
        'web',
    ],

    'data': [
        'data/data.xml',
        'report/reports.xml',
        'report/sale_order_reports.xml',
        'report/account_move_reports.xml',
        'report/stock_picking_reports.xml',
        'views/res_company_views.xml',
        'views/stock_warehouse_views.xml',
        'views/sale_order_templates.xml',
    ],
}
