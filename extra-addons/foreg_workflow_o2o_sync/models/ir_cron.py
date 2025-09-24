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
from odoo import fields, models


class IrCron(models.Model):
    _inherit = "ir.cron"

    o2o_workflow_id = fields.Many2one(
        comodel_name="foreg.o2o.workflow",
        help="The workflow associated with this scheduled action",
        ondelete="cascade",
    )
