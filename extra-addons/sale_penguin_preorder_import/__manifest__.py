{
    'name': 'Penguin Sales: pre-Order Import',
    'version': '1.2',
    'category': 'Sales/Sales',
    'summary': 'Import preorder from xls template',
    'installable': False,
    'auto_install': True,

    'depends': [
        'base_import',
        'sale_penguin',
    ],

    'data': [
        'wizard/preorder_import.xml',
    ]
}
