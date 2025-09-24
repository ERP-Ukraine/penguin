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
    "name": "4EG Cleanup Data",
    "installable": True,
    "website": "https://4egrowth.de",
    "version": "18.0.1.0.0",
    "category": "Tools",
    "sequence": 1,
    "summary": "4EG Cleanup Data",
    "author": "4E Growth GmbH",
    "depends": ["base"],
    "data": ["data/ir_cron_data.xml", "views/ir_model_views.xml"],
    "application": False,
    "license": "OPL-1",
}
