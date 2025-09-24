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
import logging

from odoo import api, models

_logger = logging.getLogger(__name__)


class ForegTrackingMixin(models.AbstractModel):
    _name = "foreg.tracking.mixin"
    _description = "Foreg Tracking Mixin"

    def get_tracking_fields(self):
        """Get list of field names to be tracked for changes.

        Base implementation returns an empty list. This method should be
        overridden in inheriting models to specify which fields should be
        tracked for changes in the chatter system.

        Returns:
            list: Empty list of field names (to be overridden by subclasses)

        Example:
            >>> tracking_fields = self.get_tracking_fields()
            >>> print(tracking_fields)
            []
        """
        return []

    @api.model
    def setup_tracking_fields(self, force=True):
        """Setup tracking configuration for specified fields in the model.

        Configures the tracking system to monitor changes on specified fields
        by enabling custom tracking on the model and its fields. The method
        checks configuration state to avoid redundant setup unless forced.
        Tracks both enabling and disabling of field tracking based on the
        current tracking field list.

        Args:
            force (bool, optional): Whether to force setup even if already
                configured. Defaults to True.

        Returns:
            bool: True when setup is completed successfully

        Example:
            >>> result = self.setup_tracking_fields(force=False)
            >>> print(result)
            True
        """
        # Check if already configured (unless forced)
        param_key = f"foreg_tracking_o2o_sync.{self._name}.configured"
        if not force and self.env["ir.config_parameter"].sudo().get_param(
            param_key, False
        ):
            _logger.info(
                f"Tracking already configured for {self._name}, skipping setup"
            )
            return True

        # Enable tracking for model
        model_rec = self.env["ir.model"].search(
            [
                ("model", "=", self._name),
                ("active_custom_tracking", "=", False),
            ]
        )
        if model_rec:
            model_rec.write(
                {
                    "active_custom_tracking": True,
                }
            )
            _logger.info(f"Enabled tracking for model {self._name}")

        # Enable tracking for specific fields
        tracking_field_names = self.get_tracking_fields()
        fields_to_track = fields_to_untrack = self.env["ir.model.fields"]
        model_fields = self.env["ir.model.fields"].search(
            [
                ("model", "=", self._name),
            ]
        )

        fields_to_track = model_fields.filtered(
            lambda f: f.name in tracking_field_names and not f.custom_tracking
        )
        fields_to_untrack = model_fields.filtered(
            lambda f: f.name not in tracking_field_names and f.custom_tracking
        )

        fields_to_track.write({"custom_tracking": True})
        fields_to_untrack.write({"custom_tracking": False})

        _logger.info(
            f"Enabled tracking for {len(fields_to_track)} "
            f"fields and disabled tracking for {len(fields_to_untrack)} fields"
        )

        # Mark as configured
        self.env["ir.config_parameter"].sudo().set_param(param_key, True)
        _logger.info(f"Tracking setup completed for {self._name}")

        return True

    @api.model
    def reset_tracking_config(self):
        """Reset tracking configuration and force re-setup.

        Clears the tracking configuration state for the current model and
        triggers a fresh setup of tracking fields. This is useful when the
        tracking field list has changed or when troubleshooting tracking
        configuration issues.

        Returns:
            bool: True when reset and re-setup is completed successfully

        Example:
            >>> result = self.reset_tracking_config()
            >>> print(result)
            True
        """
        param_key = f"foreg_tracking_o2o_sync.{self._name}.configured"
        self.env["ir.config_parameter"].sudo().set_param(param_key, False)
        _logger.info(f"Reset tracking configuration for {self._name}")
        return self.setup_tracking_fields(force=True)
