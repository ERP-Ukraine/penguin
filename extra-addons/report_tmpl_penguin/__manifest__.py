{
    'name': 'Penguin Report Template',
    'version': '1.0',
    'summary': 'Custom report header and footer for some pdf docs.',
    'installable': True,
    'auto_install': False,

    'depends': [
        'web',
        'account',
        'sale',
        'sale_stock',
    ],

    'data': [
        'report/reports.xml',
        'report/sale_order_reports.xml',
        'report/account_move_reports.xml',
        'report/stock_picking_reports.xml',
        'views/stock_warehouse_views.xml',
    ],
}
