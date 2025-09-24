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
    """Remove deprecated cron job after migration.

    This function is executed during the post-migration process. It searches for
    the deprecated scheduled action (cron job) with the external ID
    'foreg_webhook.ir_cron_gc_webhook_queue' and removes it if found. This helps
    to clean up obsolete scheduled actions that are no longer needed in the new
    version.

    Args:
        cr (Cursor): Database cursor.
        version (str): The version to which the module is being migrated.

    Returns:
        None
    """
    env = api.Environment(cr, SUPERUSER_ID, {})
    deprecated_cron = env.ref(
        "foreg_webhook.ir_cron_gc_webhook_queue", raise_if_not_found=False
    )
    if deprecated_cron:
        deprecated_cron.unlink()
