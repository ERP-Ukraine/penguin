{
    'name': 'Penguin Default Theme',
    'category': 'Theme',
    'author': 'ERP Ukraine LLC',
    'website': 'https://erp.co.ua',
    'support': 'support@erp.co.ua',
    'license': 'LGPL-3',
    'version': '1.0',
    'depends': ['website'],
    'data': [
        'data/ir_asset.xml',
    ],
    'images': [
        'static/description/theme_penguin_default_screenshot.jpg',
    ],
    'auto_install': True,
    'installable': True,
    'post_init_hook': '_post_set_footer',
}
