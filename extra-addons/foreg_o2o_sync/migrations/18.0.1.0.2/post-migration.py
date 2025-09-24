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


def migrate(cr, version):
    """Execute post-migration tasks for foreg_o2o_sync 18.0.1.0.2.

    This migration function removes deprecated cron jobs that are no longer
    needed in the new version. It safely removes the ir_cron_gc_old_request_log
    cron job if it exists.

    Args:
        env: Odoo environment instance
        version: Current module version being migrated to
    """
    env = api.Environment(cr, SUPERUSER_ID, {})
    deprecated_cron = env.ref(
        "foreg_o2o_sync.ir_cron_gc_old_request_log", raise_if_not_found=False
    )
    if deprecated_cron:
        deprecated_cron.unlink()
