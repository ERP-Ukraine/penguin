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


class SaleOrderLine(models.Model):
    """Extended Sales Order Lines with SaaS synchronization.

    This model extends the standard sales order line model to include SaaS
    synchronization functionality through the saas.mixin inheritance.
    It enables tracking of SaaS IDs and synchronization timestamps
    for sales order line records.
    """

    _name = "sale.order.line"
    _inherit = ["sale.order.line", "saas.mixin"]
