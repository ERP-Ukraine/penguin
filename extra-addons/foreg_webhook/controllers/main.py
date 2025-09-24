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
from odoo.http import Controller, request, route


class ForegWebhookController(Controller):
    @route(
        ["/foreg_webhook/<string:webhook_uuid>"],
        type="http",
        auth="public",
        methods=["GET", "POST"],
        csrf=False,
        save_session=False,
    )
    def call_webhook_http(self, webhook_uuid, **kwargs):
        """Handle incoming HTTP requests for a webhook endpoint.

        This method processes GET and POST requests to the webhook endpoint
        identified by the given webhook_uuid. It searches for the corresponding
        webhook record, and if found, creates a new queue entry with the
        incoming payload. Returns a JSON response indicating the status of the
        operation.

        Args:
            webhook_uuid (str): The unique identifier for the webhook.
            **kwargs: Additional keyword arguments from the HTTP request.

        Returns:
            werkzeug.wrappers.Response: JSON response with status and HTTP code.

        Example:
            >>> # POST or GET to /foreg_webhook/<webhook_uuid>
            >>> # Returns {"status": "ok"} if successful
        """
        webhook = (
            request.env["foreg.webhook"]
            .sudo()
            .search([("webhook_uuid", "=", webhook_uuid)])
        )
        if not webhook:
            return request.make_json_response({"status": "error"}, status=404)
        try:
            request.env["foreg.webhook.queue"].sudo().create(
                {
                    "webhook_id": webhook.id,
                    "state": "pending",
                    "payload_json": request.get_json_data(),
                }
            )
        except Exception:  # noqa: BLE001
            return request.make_json_response({"status": "error"}, status=500)
        return request.make_json_response({"status": "ok"}, status=200)
