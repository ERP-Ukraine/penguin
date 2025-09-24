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
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class SaasMixin(models.AbstractModel):
    """SaaS Mixin for O2O synchronization.

    This abstract model provides common functionality for SaaS-related models
    in the O2O synchronization system. It handles SaaS ID tracking and
    synchronization timestamps.
    """

    _name = "saas.mixin"
    _description = "SaaS Mixin"

    saas_id = fields.Integer(
        string="SaaS ID",
        help="ID from SaaS Odoo Server",
        readonly=True,
        copy=False,
    )
    lasted_sync_date_saas = fields.Datetime(
        readonly=True,
        copy=False,
        help=(
            "Timestamp of the last successful synchronization with the SaaS Odoo "
            "Server"
        ),
    )

    @api.model_create_multi
    def create(self, vals_list):
        """Create new records with SaaS synchronization tracking.

        This method overrides the default create method to automatically
        update the last synchronization date when a SaaS ID is provided.

        Args:
            vals_list (list): List of dictionaries containing field values
                for the new records

        Returns:
            recordset: Newly created records

        Example:
            >>> vals = {'name': 'Test Record', 'saas_id': 123}
            >>> record = self.create(vals)
            >>> print(record.lasted_sync_date_saas)
        """
        for vals in vals_list:
            if "saas_id" in vals:
                vals.update(
                    lasted_sync_date_saas=fields.Datetime.now().strftime(
                        DEFAULT_SERVER_DATETIME_FORMAT
                    )
                )
        return super().create(vals_list)

    def write(self, vals):
        """Update records with SaaS synchronization tracking.

        This method overrides the default write method to automatically
        update the last synchronization date when a SaaS ID is modified.

        Args:
            vals (dict): Dictionary containing field values to update

        Returns:
            bool: True if the write operation was successful

        Example:
            >>> record.write({'saas_id': 456})
            >>> print(record.lasted_sync_date_saas)
        """
        if "saas_id" in vals:
            vals.update(
                lasted_sync_date_saas=fields.Datetime.now().strftime(
                    DEFAULT_SERVER_DATETIME_FORMAT
                )
            )
        return super().write(vals)
