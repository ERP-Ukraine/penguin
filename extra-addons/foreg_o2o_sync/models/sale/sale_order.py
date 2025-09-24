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


class SaleOrder(models.Model):
    """Extended Sales Orders with SaaS synchronization.

    This model extends the standard sales order model to include SaaS
    synchronization functionality through the saas.mixin inheritance.
    It enables tracking of SaaS IDs and synchronization timestamps
    for sales order records.
    """

    _name = "sale.order"
    _inherit = ["sale.order", "saas.mixin"]

    external_id = fields.Char(
        help="External ID of the sale order in the target system",
    )
    sales_channel = fields.Char(
        help="Sales channel of the sale order",
    )
