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


class ForegO2oRequestField(models.Model):
    _name = "foreg.o2o.request.field"
    _inherit = [
        "foreg.o2o.request.field",
        "mail.thread",
        "mail.activity.mixin",
        "foreg.tracking.mixin",
    ]

    def get_tracking_fields(self):
        """Get list of O2O request field fields to be tracked for changes.

        Returns a comprehensive list of fields that should be monitored for
        changes in O2O request field configurations. This includes field
        mappings, operation usage settings, context configurations, and
        relationship settings that affect field processing behavior.

        Returns:
            list: List of field names to be tracked for changes in the chatter

        Example:
            >>> tracking_fields = self.get_tracking_fields()
            >>> print(len(tracking_fields))
            15
        """
        tracking_fields = [
            "request_id",  # Request reference changes
            "request_method",  # Operation type changes
            "model_id",  # Target model changes
            "source_field_id",  # SAAS field reference changes
            "source_field_name",  # SAAS field name changes
            "target_field_id",  # Local field reference changes
            "target_field_name",  # Local field name changes
            "is_domain_field",  # Domain usage changes
            "context",  # Context configuration changes
            "use_in_create",  # Create operation usage changes
            "use_in_write",  # Write operation usage changes
            "active",  # Active status changes
            "apply_for_root_model",  # Root model application changes
            "apply_for_relation_model",  # Relation model application changes
            # Many2many fields
            "related_field_ids",  # Related fields relationship changes
        ]
        return tracking_fields
