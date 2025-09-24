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
from odoo import api, fields, models


class IrCron(models.Model):
    _inherit = "ir.cron"

    cron_code = fields.Text(
        help="Code of the cron job."
        " This field is used to track the code of the cron job.",
    )

    def update_cron_code_vals(self, vals):
        """Update cron code tracking field when code field changes.

        Synchronizes the cron_code tracking field with the actual code field
        to maintain a trackable copy of the cron job code. This allows the
        tracking system to monitor changes to cron job implementations.

        Args:
            vals (dict): Dictionary of field values being updated

        Example:
            >>> vals = {'code': 'model.action_sync()'}
            >>> self.update_cron_code_vals(vals)
            >>> print(vals['cron_code'])
            'model.action_sync()'
        """
        if "code" in vals:
            vals["cron_code"] = vals["code"]

    def write(self, vals):
        """Write cron job fields with code tracking synchronization.

        Extends the standard write method to update the cron_code tracking
        field when the code field is modified. This ensures consistency
        between the actual code and the trackable code field.

        Args:
            vals (dict): Dictionary of field values to write

        Returns:
            bool: Result from the parent write operation

        Example:
            >>> result = cron_record.write({'code': 'new_code()'})
            >>> print("Cron updated with tracking")
        """
        self.update_cron_code_vals(vals)
        return super().write(vals)

    @api.model_create_multi
    def create(self, vals_list):
        """Create cron job records with code tracking synchronization.

        Extends the standard create method to initialize the cron_code tracking
        field when new cron jobs are created. This ensures that tracking is
        properly set up from the moment of creation.

        Args:
            vals_list (list): List of dictionaries containing field values
                for each record to create

        Returns:
            recordset: Created cron job records

        Example:
            >>> vals = [{'name': 'Test Job', 'code': 'test_method()'}]
            >>> new_crons = self.create(vals)
            >>> print("Cron jobs created with tracking")
        """
        for vals in vals_list:
            self.update_cron_code_vals(vals)
        return super().create(vals_list)
