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
from openupgradelib import openupgrade

from odoo.tools import convert_file


@openupgrade.migrate()
def migrate(env, version):
    """Execute post-migration tasks for foreg_o2o_sync 17.0.1.0.3.

    This migration function converts the ir_model_data.xml file to ensure
    proper data initialization after the module upgrade.

    Args:
        env: Odoo environment instance
        version: Current module version being migrated to
    """
    convert_file(
        env,
        "foreg_o2o_sync",
        "data/ir_model_data.xml",
        None,
        mode="init",
        noupdate=False,
    )
