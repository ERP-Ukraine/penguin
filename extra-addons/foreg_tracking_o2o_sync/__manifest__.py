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
    "name": "4EG Tracking Odoo to Odoo Synchronization",
    "version": "18.0.1.0.0",  # Previous version 17.0.1.0.0
    "category": "Connector",
    "author": "4E Growth GmbH",
    "maintainer": "Duc, DAO",
    "license": "OPL-1",
    "website": "https://4egrowth.de",
    "live_test_url": "https://demo.fouregrowth.com/contactus",
    "summary": """
        Enhanced tracking and auditing for O2O synchronization with chatter
        integration and detailed change history.
    """,
    # Dependencies
    "depends": [
        "foreg_o2o_sync",
        # oca-server-tools
        "tracking_manager",
    ],
    "images": [],
    "data": [
        # Security
        # Data
        "data/tracking_config_data.xml",
        # Views
        "views/foreg_o2o_instance_chatter_views.xml",
        "views/foreg_o2o_instance_fixed_value_chatter_views.xml",
        "views/foreg_o2o_request_chatter_views.xml",
        "views/foreg_o2o_request_field_chatter_views.xml",
    ],
    "installable": False,
    "application": False,
    "price": 9999.00,
    "currency": "EUR",
    "support": "4egrowth@gmail.com",
}
