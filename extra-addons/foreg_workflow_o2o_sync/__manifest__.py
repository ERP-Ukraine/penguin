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
    "name": "4EG Workflow Odoo to Odoo Sync",
    "version": "18.0.1.0.0",  # Previous version 17.0.1.0.0
    "summary": "Dynamic and extensible workflow system for API calls",
    "category": "Tools",
    "author": "4E Growth GmbH",
    "website": "https://4egrowth.de",
    "license": "OPL-1",
    "depends": ["base", "foreg_o2o_sync"],
    "data": [
        "security/ir.model.access.csv",
        "views/foreg_o2o_workflow_views.xml",
        "views/foreg_o2o_workflow_job_views.xml",
        "views/menu_views.xml",
    ],
    "demo": [],
    "installable": False,
    "auto_install": False,
    "application": False,
}
