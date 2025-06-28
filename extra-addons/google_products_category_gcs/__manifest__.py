# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
#################################################################################
# Author      : Grow Consultancy Services (<https://www.growconsultancyservices.com/>)
# Copyright(c): 2021-Present Grow Consultancy Services
# All Rights Reserved.
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
#################################################################################
{
    # Application Information
    'name': 'Google Product Categories GCS',
    'version': '15.0.0',
    'category': 'Sales',
    'license': 'OPL-1',

    # Summary Informations
    # Summary: Approx 200 Char
    # Description:
    'summary': """
        Google Product Categories GCS
    """,
    'description': """
        Google Product Categories GCS
    """,

    # Author Information
    'author': 'Grow Consultancy Services',
    'maintainer': 'Grow Consultancy Services',
    'website': 'http://www.growconsultancyservices.com',

    # Application Price Information
    'price': 5,
    'currency': 'EUR',

    # Dependencies
    'depends': ['base', 'product', 'sale_management'],

    # Views
    'data': [
        "security/ir.model.access.csv",
        "views/google_product_category_gcs_views.xml",
        "views/product_template_views.xml",
        "wizard/import_google_product_categories_wizard_views.xml",
        # 'view/'
        # wizard/
    ],

    # Application Main Image
    'images': ['static/description/app_profile_image.jpg'],

    # Technical
    'installable': False,
    'application': True,
    'auto_install': False,
    'active': False,
}
