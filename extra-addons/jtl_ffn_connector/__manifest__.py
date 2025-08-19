# -*- coding: utf-8 -*-
{
    'name': "Odoo JTL FFN Connector",
    'summary': "Odoo JTL FFN Connector",
    'description': """Odoo JTL FFN Connector""",
    'author': "Tecsee",
    'website': "https://tecsee.de",
    'category': 'Inventory/Connector',
    'version': '0.2',
    'depends': ['base', 'stock', 'sale', 'purchase', 'delivery'],

    'license': 'OPL-1',
    'price': 550,
    'currency' 'EUR'
    'images': ['images/main1_screenshot.png'],

    'data': [
        'security/ir.model.access.csv',
        'data/cron.xml',
        'views/res_company.xml',
        'views/res_partner.xml',
        'views/product_template.xml',
        'views/stock_warehouse.xml',
        'views/delivery_carrier.xml',
        'views/purchase_order.xml',
        'views/sale_order.xml',
        'wizards/ffn_connector.xml',
        'wizards/ffn_authorize.xml',
    ],
}

