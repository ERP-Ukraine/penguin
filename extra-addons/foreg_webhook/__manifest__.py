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
    "name": "4EG Webhook",
    "version": "18.0.1.0.2",
    "category": "Tools",
    "author": "4E Growth GmbH",
    "maintainer": "Duc, DAO",
    "license": "OPL-1",
    "website": "https://4egrowth.de",
    "live_test_url": "https://demo.fouregrowth.com/contactus",
    "summary": """
    """,
    # Dependencies
    "depends": [
        "base",
        "foreg_cleanup_data",
    ],
    "images": [],
    "data": [
        # Data
        "data/foreg_webhook_code_template_data.xml",
        "data/ir_cron_data.xml",
        "data/ir_model_data.xml",
        # Security
        "security/ir.model.access.csv",
        # Views
        "views/foreg_webhook_views.xml",
        "views/foreg_webhook_queue_views.xml",
        "views/foreg_webhook_code_template_views.xml",
        "views/menu.xml",
    ],
    "installable": True,
    "external_dependencies": {},
    "application": True,
    "price": 9999.00,
    "currency": "EUR",
    "support": "4egrowth@gmail.com",
    "sequence": -100,
}
