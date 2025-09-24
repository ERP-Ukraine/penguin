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


class IrActionsServer(models.Model):
    """Extended Server Actions for O2O synchronization.

    This model extends the standard server actions to include O2O request
    associations, enabling automated O2O operations through server actions.
    """

    _inherit = "ir.actions.server"

    o2o_request_id = fields.Many2one(
        comodel_name="foreg.o2o.request",
        string="O2O Request",
        ondelete="cascade",
        help="O2O request associated with this action server",
    )
