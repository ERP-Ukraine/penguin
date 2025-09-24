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


class ForegO2oInstanceFixedValue(models.Model):
    _name = "foreg.o2o.instance.fixed.value"
    _inherit = [
        "foreg.o2o.instance.fixed.value",
        "mail.thread",
        "mail.activity.mixin",
        "foreg.tracking.mixin",
    ]

    def get_tracking_fields(self):
        """Get list of fixed value fields to be tracked for changes.

        Returns the list of fields that should be monitored for changes in
        O2O instance fixed value configurations. This includes the instance
        reference, model and field mappings, the actual value, and active
        status to track all aspects of fixed value management.

        Returns:
            list: List of field names to be tracked for changes in the chatter

        Example:
            >>> tracking_fields = self.get_tracking_fields()
            >>> print(len(tracking_fields))
            5
        """
        tracking_fields = [
            "instance_id",  # Instance reference changes
            "model_id",  # Target model changes
            "field_id",  # Target field changes
            "value",  # Fixed value changes
            "active",  # Active status changes
        ]
        return tracking_fields
