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
from datetime import timedelta

import requests

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import format_datetime
from odoo.tools.json import scriptsafe as json_scriptsafe
from odoo.tools.safe_eval import safe_eval

_logger = logging.getLogger(__name__)


class ForegWebhookQueue(models.Model):
    _name = "foreg.webhook.queue"
    _description = "4EG Webhook Queue"
    _order = "create_date DESC"

    webhook_id = fields.Many2one(
        comodel_name="foreg.webhook",
        required=True,
        help="Webhook that the log belongs to",
        ondelete="cascade",
    )
    webhook_trigger = fields.Selection(
        related="webhook_id.trigger",
        store=True,
        help="Trigger of the webhook",
    )
    state = fields.Selection(
        selection=[
            ("pending", "Pending"),
            ("retry", "Retry"),
            ("passed", "Passed"),
            ("failed", "Failed"),
        ],
        default="pending",
        required=True,
        readonly=True,
        help="State of the log",
    )
    retry_count = fields.Integer(
        default=0,
        readonly=True,
        help="Number of retry attempts made",
    )
    max_retries = fields.Integer(
        related="webhook_id.max_retries",
        readonly=True,
        help="Maximum number of retry attempts allowed",
    )
    next_retry = fields.Datetime(
        help="Next scheduled retry time",
        readonly=True,
    )
    error_message = fields.Text(
        help="Error message of the webhook",
        readonly=True,
    )
    payload_json = fields.Json(
        help="Payload of the webhook (raw)",
        readonly=True,
    )
    payload = fields.Text(
        help="Payload of the webhook (formatted)",
        compute="_compute_payload",
        readonly=True,
    )

    @api.depends("create_date", "webhook_id", "state")
    def _compute_display_name(self):
        """Compute the display name for the webhook queue record.

        The display name is composed of the creation date, webhook name, and
        current state. This method is triggered when any of the dependent
        fields change.
        """
        for record in self:
            record.display_name = (
                f"{format_datetime(record.env, record.create_date)} - "
                f"{record.webhook_id.name} - {record.state}"
            )

    @api.depends("payload_json")
    def _compute_payload(self):
        """Compute the formatted payload from the JSON payload.

        Converts the JSON payload to a pretty-printed string for display
        purposes. If conversion fails, falls back to string representation.
        """
        for record in self:
            try:
                record.payload = json.dumps(record.payload_json, indent=2)
            except Exception:
                record.payload = str(record.payload_json)

    def process_webhook_queue(self, force_run=False):
        """Process the webhook queue for each grouped webhook.

        Sends the payload to the webhook URL or executes custom code based on
        the trigger. Updates the state of each record accordingly. Handles
        errors and manages retries.

        Args:
            force_run (bool, optional): If True, forces processing regardless
                of state. Defaults to False.
        """
        for webhook, records in self.grouped("webhook_id").items():
            _logger.info(
                f"Processing webhook {webhook.name} with {len(records)} records"
            )
            vals = {
                "state": "passed",
            }
            try:
                if webhook.trigger in [
                    "on_write",
                    "on_create",
                    "on_unlink",
                    "on_modification",
                ]:
                    response = requests.post(
                        webhook.url,
                        json=records.combine_payload_json(),
                        timeout=10,
                    )
                    response.raise_for_status()
                elif webhook.trigger == "on_webhook" and self.text_contains_code(
                    webhook.code
                ):
                    records.compute_python_code()
                records.sudo().write(vals)
            except Exception as e:
                for record in records:
                    vals.update(record._handle_webhook_failure(e))
                    record.sudo().write(vals)

    def _handle_webhook_failure(self, error):
        """Handle webhook failure and determine if retry is needed.

        Updates the error message and sets the state to 'failed' if the maximum
        number of retries has been reached, otherwise schedules a retry.

        Args:
            error (Exception): The exception that occurred during processing.

        Returns:
            dict: Values to update on the record (error message, state, retry
                count, next retry time).
        """
        self.ensure_one()
        vals = {
            "error_message": str(error),
        }

        if self.retry_count >= self.max_retries:
            vals["state"] = "failed"
        else:
            vals.update(
                {
                    "state": "retry",
                    "retry_count": self.retry_count + 1,
                    "next_retry": self._calculate_next_retry_time(),
                }
            )
        return vals

    def _calculate_next_retry_time(self):
        """Calculate the next retry time using exponential backoff.

        The delay is based on the webhook's retry interval and the current
        retry count, using exponential backoff.

        Returns:
            datetime: The next retry datetime.
        """
        self.ensure_one()
        # Exponential backoff based on webhook's retry interval
        delay_minutes = self.webhook_id.retry_interval * (5 ** (self.retry_count - 1))
        return fields.Datetime.now() + timedelta(minutes=delay_minutes)

    def cron_process_webhook_queue(self):
        """Scheduled cron job to process pending and retry webhook queue items.

        Searches for records in 'pending' or 'retry' state (with next_retry
        due) and processes them.
        """
        domain = [
            "|",
            "&",
            ("state", "=", "pending"),
            ("next_retry", "=", False),
            "&",
            ("state", "=", "retry"),
            ("next_retry", "<=", fields.Datetime.now()),
        ]
        self.env["foreg.webhook.queue"].search(domain).process_webhook_queue()

    def action_retry(self):
        """Manual action to retry failed or retrying webhooks.

        Resets the state to 'pending' and clears the next retry time, then
        processes the queue.
        """
        self.filtered(lambda r: r.state in ["failed", "retry"]).write(
            {
                "state": "pending",
                "next_retry": False,
            }
        )
        self.process_webhook_queue()

    def action_process_webhook_queue(self, force_run=False):
        """Manual action to process the webhook queue.

        Args:
            force_run (bool, optional): If True, forces processing regardless
                of state. Defaults to False.
        """
        self.process_webhook_queue(force_run=force_run)

    @staticmethod
    def text_contains_code(text):
        """Check if the given text contains executable code (not just comments).

        Args:
            text (str): The text to check.

        Returns:
            bool: True if the text contains code, False otherwise.
        """
        if not text:
            return False
        return any(
            line.strip() and not line.strip().startswith("#")
            for line in text.splitlines()
        )

    def compute_python_code(self):
        """Execute custom Python code for the webhook using safe_eval.

        The code is executed in a safe context with access to the environment,
        logger, payload, and Odoo's evaluation context.
        """
        self.webhook_id.ensure_one()
        local_dict = {
            "env": self.env,
            "json": json_scriptsafe,
            "UserError": UserError,
            "ValidationError": ValidationError,
            "log": _logger,
            "payload": self.combine_payload_json(),
            **self.env["ir.actions.actions"]._get_eval_context(),
        }
        safe_eval(self.webhook_id.code, local_dict, mode="exec", nocopy=True)

    def combine_payload_json(self):
        """Combine consecutive webhook payloads with the same model and method.

        Only merges payloads that are adjacent in the queue to maintain
        operation order. Returns a list of payloads where consecutive similar
        entries are merged.

        Returns:
            list: List of merged payloads.
        """
        if not self:
            return []

        # Sort records by creation date to maintain chronological order
        sorted_records = self.sorted("create_date")

        result = []
        current_payload = None

        for record in sorted_records:
            if not record.payload_json:
                continue

            if isinstance(record.payload_json, dict):
                result.append(record.payload_json)
                continue

            for payload in record.payload_json:
                if not current_payload:
                    current_payload = payload.copy()
                    continue

                # Check if current payload can be merged with previous one
                if payload.get("model") == current_payload.get("model") and payload.get(
                    "method"
                ) == current_payload.get("method"):
                    # Merge IDs for consecutive similar payloads
                    current_payload["ids"].extend(payload.get("ids", []))
                    # Remove duplicates while preserving order
                    current_payload["ids"] = list(dict.fromkeys(current_payload["ids"]))
                else:
                    # Different payload type, add current to result and start new one
                    result.append(current_payload)
                    current_payload = payload.copy()

        # Add the last payload if exists
        if current_payload:
            result.append(current_payload)

        return result
