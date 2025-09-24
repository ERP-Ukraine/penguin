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
from odoo import SUPERUSER_ID, api
from odoo.tools import convert_file


def migrate(cr, version):
    """Execute post-migration tasks for foreg_o2o_sync module.

    This migration function loads the ir_model_data.xml file to ensure
    proper data initialization after the module upgrade. The file is
    loaded in 'init' mode with noupdate=False to force updates.

    Args:
        cr: Database cursor for executing operations
        version (str): Current version being migrated to
    """
    env = api.Environment(cr, SUPERUSER_ID, {})
    convert_file(
        env,
        "foreg_o2o_sync",
        "data/ir_model_data.xml",
        None,
        mode="init",
        noupdate=False,
    )
