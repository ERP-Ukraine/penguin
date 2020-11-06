# -*- coding: utf-8 -*-
{
    'name': 'Penguin Product Availability',
    'version': '13.0.1.1',
    'category': 'Website/Website',
    'summary': 'Manage product inventory & availability',
    'description': """""",
    'depends': [
        'website_sale_penguin',
        'website_sale_stock',
    ],
    'data': [
        'report/report_deliveryslip.xml',
        'views/product_views.xml'
    ],
    'demo': [],
    'auto_install': True,
    'post_init_hook': 'set_inventory_availability_on_product_templates'
}
