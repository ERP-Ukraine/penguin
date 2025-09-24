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

import json
from datetime import date, datetime

from odoo import api, fields, models
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT


class ForegO2oRequestRecord(models.Model):
    """4EG O2O Request Record for tracking synchronized data.

    This model tracks individual records that are created or updated
    during O2O synchronization operations, including the operation type,
    target model, and processed values.
    """

    _name = "foreg.o2o.request.record"
    _description = "4EG O2O Request Record"

    @api.model
    def _selection_target_model(self):
        """Get selection options for target models.

        This method provides a list of available models for selection
        in the res_ref field, used for dynamic record references.

        Returns:
            list: List of tuples with (model_name, model_description)

        Example:
            >>> models = self._selection_target_model()
            >>> print(models)
        """
        return [
            (model.model, model.name)
            for model in self.env["ir.model"].sudo().search([])
        ]

    log_id = fields.Many2one(
        comodel_name="foreg.o2o.request.log",
        required=True,
        ondelete="cascade",
        index=True,
        help="Reference to the O2O request log entry that contains this record",
    )
    method_applied = fields.Selection(
        selection=[
            ("create", "Create"),
            ("write", "Write"),
        ],
        required=True,
        help="The type of operation performed on the record (create or update)",
    )
    res_model = fields.Char(
        string="Related Record Model Name",
        required=True,
        index=True,
        help="Technical name of the model for the synchronized record",
    )
    res_id = fields.Many2oneReference(
        string="Related Record ID",
        index=True,
        model_field="res_model",
        help=(
            "Database ID of the synchronized record. "
            "Used in combination with the model "
            "name to reference the record"
        ),
    )
    res_ref = fields.Reference(
        string="Related Record",
        selection="_selection_target_model",
        compute="_compute_res_ref",
        help="Dynamic reference to the synchronized record combining model and ID",
    )
    process_values_json = fields.Json(
        help="Raw JSON data containing the values used for record creation or update"
    )
    process_values = fields.Text(
        compute="_compute_json_preview",
        help="Human-readable formatted version of the process values JSON data",
    )

    @api.depends()
    def _compute_res_ref(self):
        """Compute the reference string for the related record.

        This method combines the model name and record ID to create
        a reference string that can be used to access the related record.

        Example:
            >>> record._compute_res_ref()
            >>> print(record.res_ref)  # Output: 'res.partner,123'
        """
        for rec in self:
            rec.res_ref = (
                f"{rec.res_model},{rec.res_id}"
                if rec.res_model and rec.res_id
                else None
            )

    @api.depends("process_values_json")
    def _compute_json_preview(self):
        """Compute formatted JSON preview for process values.

        This method converts the raw JSON data into a human-readable
        formatted string for display in the user interface.

        Example:
            >>> record._compute_json_preview()
            >>> print(record.process_values)
        """
        for rec in self:
            rec.process_values = json.dumps(
                rec.process_values_json or {}, sort_keys=True, indent=2
            )

    @api.model_create_multi
    def create(self, vals_list):
        """Create new request record entries with formatted datetime values.

        This method overrides the default create method to ensure that
        datetime and date values in process_values_json are properly
        formatted before storage.

        Args:
            vals_list (list): List of dictionaries containing field values

        Returns:
            recordset: Newly created request record entries

        Example:
            >>> vals = {'process_values_json': {'date_field': datetime.now()}}
            >>> record = self.create(vals)
        """
        for vals in vals_list:
            for field_name, field_value in vals.get("process_values_json", {}).items():
                if isinstance(field_value, datetime):
                    vals["process_values_json"][field_name] = field_value.strftime(
                        DEFAULT_SERVER_DATETIME_FORMAT
                    )
                elif isinstance(field_value, date):
                    vals["process_values_json"][field_name] = field_value.strftime(
                        DEFAULT_SERVER_DATE_FORMAT
                    )
        return super().create(vals_list)
