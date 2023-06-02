{
    'name': 'Account Penguin',
    'summary': 'Penguin accounting customizations',
    'author': 'ERP Ukraine',
    'website': 'https://erp.co.ua',
    'support': 'support@erp.co.ua',
    'license': 'LGPL-3',
    'category': 'Accounting/Accounting',
    'version': '2.1',
    'depends': ['account'],
    'data': [
        'report/report_invoice.xml',
        'views/account_move_views.xml'
    ],
    'application': False,
    'installable': True,
    'auto_install': True,
}
