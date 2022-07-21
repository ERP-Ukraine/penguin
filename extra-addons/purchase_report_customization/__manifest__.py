{
    'name': 'Purchase Report Customization',
    'summary': 'Penguin purhcase order customization',
    'author': 'ERP Ukraine LLC',
    'website': 'https://erp.co.ua',
    'support': 'support@erp.co.ua',
    'license': 'LGPL-3',
    'category': 'Inventory/Purchase',
    'version': '1.0',
    'depends': ['purchase'],
    'data': [
        'report/purchase_quotation_templates.xml',
        'report/purchase_order_templates.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
