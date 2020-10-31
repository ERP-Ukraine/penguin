{
    'name': 'Penguin Sales: pre-Order Import',
    'version': '1.0',
    'category': 'Sales/Sales',
    'summary': 'Import preorder from xls template',
    'installable': True,
    'auto_install': True,

    'depends': [
        'base_import',
        'sale_penguin',
    ],

    'data': [
        'wizard/preorder_import.xml',
    ]
}
