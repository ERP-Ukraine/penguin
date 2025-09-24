###############################################################################
#
#    Copyright (C) 2024-TODAY 4E Growth GmbH (<https://4egrowth.de>)
#    All Rights Reserved.
#
#    This software is proprietary and confidential. Unauthorized copying,
#    modification, distribution, or use of this software, via any medium,
#    is strictly prohibited without the express written permission of
#    4E Growth GmbH.
#
#    This software is provided under a license agreement and may be used
#    only in accordance with the terms of said agreement.
#
###############################################################################

{
    "name": "4EG Odoo to Odoo Synchronization",
    "version": "18.0.1.0.3",
    "category": "Connector",
    "author": "4E Growth GmbH",
    "maintainer": "Duc, DAO",
    "license": "OPL-1",
    "website": "https://4egrowth.de",
    "live_test_url": "https://demo.fouregrowth.com/contactus",
    "summary": """
    """,
    # Dependencies
    "depends": [
        "mail",
        "product",
        "account",
        "sale",
        "stock",
        "foreg_cleanup_data",
    ],
    "images": [],
    "data": [
        # Security
        "security/ir.model.access.csv",
        # Views
        "views/foreg_o2o_instance_views.xml",
        "views/foreg_o2o_request_views.xml",
        "views/foreg_o2o_request_field_views.xml",
        "views/foreg_o2o_request_log_views.xml",
        "views/foreg_o2o_request_record_views.xml",
        "views/o2o_shops_menus.xml",
        "views/product_product_views.xml",
        "views/res_partner_views.xml",
        "views/sale_order_views.xml",
        "views/ir_model_fields_views.xml",
        # Wizards
        "wizards/foreg_saas_operation_wizard_views.xml",
        "wizards/foreg_copy_field_wizard_views.xml",
        # Menu
        "views/menu.xml",
        # Cron
        "data/ir_cron_data.xml",
        "data/ir_model_data.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "foreg_o2o_sync/static/src/views/fields/domain/domain_field.xml",
        ],
    },
    "installable": True,
    "application": True,
    "price": 9999.00,
    "currency": "EUR",
    "support": "4egrowth@gmail.com",
    "external_dependencies": {
        "python": ["openupgradelib"],
    },
}
