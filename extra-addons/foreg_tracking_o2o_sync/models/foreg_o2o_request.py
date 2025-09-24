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


class ForegO2oRequest(models.Model):
    _name = "foreg.o2o.request"
    _inherit = [
        "foreg.o2o.request",
        "mail.thread",
        "mail.activity.mixin",
        "foreg.tracking.mixin",
    ]

    def get_tracking_fields(self):
        """Get list of O2O request fields to be tracked for changes.

        Returns a comprehensive list of fields that should be monitored for
        changes in O2O request configurations. This includes execution settings,
        filtering criteria, data manipulation parameters, relationships, and
        other critical fields that affect request processing behavior.

        Returns:
            list: List of field names to be tracked for changes in the chatter

        Example:
            >>> tracking_fields = self.get_tracking_fields()
            >>> print(len(tracking_fields))
            24
        """
        tracking_fields = [
            "sequence",  # Execution order changes
            "name",  # Request name changes
            "method",  # Request method changes
            "model_id",  # Target model changes
            "instance_id",  # Target instance changes
            "url",  # Endpoint URL changes
            "id_record",  # Specific record ID changes
            "read_filter",  # Filter criteria changes
            "read_offset",  # Offset changes
            "read_offset_step",  # Offset step changes
            "read_limit",  # Record limit changes
            "read_order",  # Sorting criteria changes
            "read_exclude_fields",  # Excluded fields changes
            "read_include_fields",  # Included fields changes
            "values",  # Values for create/update changes
            "method_name",  # Method name changes
            "timeout",  # Timeout setting changes
            "server_action_id",  # Server action reference changes
            "mail_template_id",  # Mail template reference changes
            "context",  # Context configuration changes
            "active",  # Active status changes
            # Many2many and One2many fields
            "field_ids",  # All request fields relationship changes
            "cron_ids",  # Scheduled jobs relationship changes
        ]
        return tracking_fields

    def unlink(self):
        """Delete O2O request records with chatter notification.

        Extends the standard unlink behavior to post deletion notifications
        to the related O2O instance's chatter. This provides audit trail
        visibility when requests are removed from the system.

        Returns:
            bool: Result from the parent unlink operation

        Example:
            >>> result = request_record.unlink()
            >>> print("Request deleted with notification")
        """
        for record in self:
            record.instance_id.message_post(
                body=(
                    f"Request {record.name} of model "
                    f"{record.model_id.name} has been deleted"
                ),
            )
        return super().unlink()
