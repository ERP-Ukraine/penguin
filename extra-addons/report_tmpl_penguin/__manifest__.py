{
    'name': 'Penguin Report Template',
    'version': '1.2',
    'summary': 'Custom report header and footer for some pdf docs.',
    'installable': True,
    'auto_install': False,

    'depends': [
        'base',
        'web',
        'account',
        'sale',
        'sale_stock',
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
