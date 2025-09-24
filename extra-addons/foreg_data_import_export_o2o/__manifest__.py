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
    "name": "4EG Data Import Export O2O",
    "summary": "Import and export data in JSON format with XML ID support",
    "author": "4E Growth GmbH",
    "website": "https://4egrowth.de",
    "category": "Tools",
    "version": "18.0.1.0.0",  # Previous version 17.0.1.0.0
    "depends": [
        "foreg_o2o_sync",
        "foreg_data_import_export",
    ],
    "data": [
        "data/ir_config_parameter.xml",
        # Views
        "views/foreg_data_import_export_views.xml",
    ],
    "installable": False,
    "application": False,
    "license": "OPL-1",
}
