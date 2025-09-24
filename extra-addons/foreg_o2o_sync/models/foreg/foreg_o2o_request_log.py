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
import logging

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class ForegO2oRequestLog(models.Model):
    """4EG O2O Request Log for tracking synchronization operations.

    This model logs the execution of O2O requests, including timing,
    success/failure status, request parameters, responses, and detailed
    execution logs for debugging and audit purposes.
    """

    _name = "foreg.o2o.request.log"
    _description = "4EG O2O Request Log"
    _order = "create_date desc"

    request_id = fields.Many2one(
        comodel_name="foreg.o2o.request",
        required=True,
        ondelete="cascade",
        help="Reference to the O2O request that generated this log entry",
    )
    execution_time = fields.Char(
        string="Execution Time (seconds)",
        help="Time taken to execute the request in seconds",
    )
    state = fields.Selection(
        selection=[("pass", "Passed"), ("fail", "Failed")],
        help="Status of the request execution - either passed or failed",
    )
    request_kwargs = fields.Text(
        compute="_compute_json_preview",
        help="Formatted display of the request parameters and arguments",
    )
    request_kwargs_json = fields.Json(
        help="Raw JSON data containing the request parameters and arguments",
    )
    response = fields.Text(
        compute="_compute_json_preview",
        help="Formatted display of the API response",
    )
    response_json = fields.Json(
        help="Raw JSON data containing the complete API response",
    )
    logs = fields.Html(
        help="Detailed execution logs and debug information in HTML format",
    )
    record_ids = fields.One2many(
        comodel_name="foreg.o2o.request.record",
        inverse_name="log_id",
        help="Related request records associated with this log entry",
    )
    model_record_ids = fields.One2many(
        comodel_name="foreg.o2o.request.record",
        inverse_name="log_id",
        compute="_compute_model_record_ids",
        help="Filtered request records specific to the current model",
    )
    read_filter = fields.Char(
        readonly=True,
        help="Filter criteria used for reading records during the request",
    )
    model = fields.Char(
        readonly=True,
        help="Technical name of the model associated with this request log",
    )

    @api.depends("request_kwargs_json", "response_json")
    def _compute_json_preview(self):
        """Compute formatted JSON previews for request and response data.

        This method formats the raw JSON data into readable text for
        display in the user interface.

        Example:
            >>> log._compute_json_preview()
            >>> print(log.request_kwargs)
        """
        for rec in self:
            rec.request_kwargs = json.dumps(
                rec.request_kwargs_json or {}, sort_keys=True, indent=2
            )
            rec.response = json.dumps(rec.response_json or {}, sort_keys=True, indent=2)

    @api.depends("record_ids", "model")
    def _compute_model_record_ids(self):
        """Compute model-specific record IDs for filtering.

        This method filters request records based on the current model
        to show only relevant records in the user interface.

        Example:
            >>> log._compute_model_record_ids()
            >>> print(log.model_record_ids)
        """
        for rec in self:
            records = self.record_ids
            if rec.model:
                records = records.filtered(lambda r, m=rec.model: r.res_model == m)
            rec.model_record_ids = records

    def action_display_notification(self, success_message=False, fail_message=False):
        """Display notification based on request execution status.

        This method shows a success or failure notification based on
        the request execution state, with customizable messages.

        Args:
            success_message (str, optional): Custom success message.
                Defaults to auto-generated message.
            fail_message (str, optional): Custom failure message.
                Defaults to auto-generated message.

        Returns:
            dict: Client action for displaying notification

        Example:
            >>> log.action_display_notification(
            ...     success_message="Custom success message"
            ... )
        """
        self.ensure_one()

        if not success_message:
            success_message = f"{self.request_id.url} successfully!"

        if not fail_message:
            fail_message = f"{self.request_id.url} failed!"

        if self.state == "pass":
            message_type = "success"
            message = success_message
        else:
            message_type = "danger"
            message = fail_message

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "message": message,
                "type": message_type,
                "sticky": False,
                "next": {"type": "ir.actions.act_window_close"},
            },
        }

    def action_view_full(self):
        """Open full log view in a new window.

        This method opens the complete log record in a new popup
        window for detailed viewing and editing.

        Returns:
            dict: Action window definition for the full log view

        Example:
            >>> action = log.action_view_full()
        """
        self.ensure_one()
        return {
            "name": _("Log"),
            "type": "ir.actions.act_window",
            "res_model": "foreg.o2o.request.log",
            "view_mode": "form",
            "target": "new",
            "res_id": self.id,
        }

    def action_view_log(self):
        """Open log-only view in a new window.

        This method opens a simplified log view that shows only
        the log information without additional details.

        Returns:
            dict: Action window definition for the log-only view

        Example:
            >>> action = log.action_view_log()
        """
        self.ensure_one()
        return {
            "name": _("Log"),
            "type": "ir.actions.act_window",
            "res_model": "foreg.o2o.request.log",
            "view_mode": "form",
            "target": "new",
            "res_id": self.id,
            "views": [
                (
                    self.env.ref(
                        "foreg_o2o_sync.foreg_o2o_request_log_view_form_log_only"
                    ).id,
                    "form",
                )
            ],
        }
