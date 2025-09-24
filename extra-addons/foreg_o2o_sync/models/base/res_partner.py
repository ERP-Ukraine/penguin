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

from odoo import models


class ResPartner(models.Model):
    """Extended Partners with SaaS synchronization capabilities.

    This model extends the standard partner model to include SaaS
    synchronization functionality through the saas.mixin inheritance.
    It enables tracking of SaaS IDs and synchronization timestamps
    for partner records.
    """

    _name = "res.partner"
    _inherit = ["res.partner", "saas.mixin"]
