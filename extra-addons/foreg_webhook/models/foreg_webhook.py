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
import uuid
from collections import defaultdict

from odoo import api, fields, models

STANDARD_DEFAULT_PYTHON_CODE = """# Common variables
#  - env: Odoo Environment on which the action is triggered
#  - uid: current user id
#  - user: current res.user
#  - payload: webhook payload
# Python lib:
#  - datetime
#  - json
#  - time
#  - dateutil
#  - timezone
#  - b64encode
#  - b64decode
# Odoo function
#  - Command
#  - float_compare
#  - UserError
#  - ValidationError
#  - log
"""

_logger = logging.getLogger(__name__)


class ForegWebhook(models.Model):
    _name = "foreg.webhook"
    _description = "4EG Webhook"

    def _default_webhook_uuid(self):
        """Generate a new UUID string for the webhook.

        This method is used as the default value generator for the webhook_uuid
        field, ensuring each webhook has a unique identifier.

        Returns:
            str: A new UUID string.
        """
        return str(uuid.uuid4())

    name = fields.Char(
        required=True,
        help="Name of the webhook",
    )
    description = fields.Text(
        help="Description of the webhook",
    )
    trigger = fields.Selection(
        selection=[
            ("on_create", "On Create"),
            ("on_write", "On Write"),
            ("on_unlink", "On Unlink"),
            ("on_modification", "On Modification"),
            ("on_webhook", "On Webhook"),
        ],
        required=True,
        default="on_create",
        help=(
            "Trigger type that determines when the webhook will be executed:\n"
            "- On Create: Triggered when a new record is created\n"
            "- On Write: Triggered when a record is modified\n"
            "- On Unlink: Triggered when a record is deleted\n"
            "- On Modification: Triggered for both creation and modification\n"
            "- On Webhook: Triggered by an external webhook call"
        ),
    )
    model_id = fields.Many2one(
        comodel_name="ir.model",
        string="Model",
        help="Model that the webhook will be triggered on",
    )
    url = fields.Char(
        compute="_compute_url",
        readonly=False,
        store=True,
        help="URL of the webhook",
    )
    webhook_uuid = fields.Char(
        string="Webhook UUID",
        readonly=True,
        copy=False,
        default=_default_webhook_uuid,
        help="UUID of the webhook",
    )
    active = fields.Boolean(
        default=True,
        help="Whether the webhook is active",
    )
    queue_ids = fields.One2many(
        comodel_name="foreg.webhook.queue",
        inverse_name="webhook_id",
        help="Queues of the webhook",
    )
    template_id = fields.Many2one(
        comodel_name="foreg.webhook.code.template",
        help="Template of the webhook. Select to apply a template to the webhook.",
    )
    code = fields.Text(
        help=("Python code that will be executed when the webhook is triggered."),
        default=STANDARD_DEFAULT_PYTHON_CODE,
    )
    max_retries = fields.Integer(
        string="Maximum Retries",
        default=3,
        required=True,
        help="Maximum number of retry attempts allowed for failed webhook calls",
    )
    retry_interval = fields.Integer(
        string="Initial Retry Interval (minutes)",
        default=5,
        required=True,
        help=(
            "Initial interval in minutes between retry attempts. This interval will "
            "increase exponentially with each retry."
        ),
    )

    @api.depends("trigger", "webhook_uuid")
    def _compute_url(self):
        """Compute the webhook URL based on the trigger and UUID.

        This method updates the 'url' field. If the trigger is 'on_webhook',
        it constructs the URL using the base URL and the webhook UUID. If the
        UUID is present in the current URL but the trigger is not 'on_webhook',
        it clears the URL.
        """
        for record in self:
            url = record.url or ""
            if record.trigger == "on_webhook":
                url = f"{record.get_base_url()}/foreg_webhook/{record.webhook_uuid}"
            elif (record.webhook_uuid or "") in url:
                url = ""
            record.url = url

    @api.onchange("template_id")
    def _onchange_template_id(self):
        """Update the code field when a template is selected.

        This method is triggered when the 'template_id' field changes. If a
        template is selected, its code is copied to the webhook's code field.
        """
        if self.template_id:
            self.code = self.template_id.code

    def _register_hook(self):
        """Patch Odoo model methods to trigger webhooks on create, write, unlink.

        This method dynamically patches the 'create', 'write', and 'unlink'
        methods of all models (except TransientModels) to automatically create
        webhook queues when the corresponding actions occur, according to the
        webhook's trigger configuration.
        """

        def make_create():
            """Create a patched create method for webhook triggering.

            This function creates a patched version of the create method that
            automatically triggers webhooks when records are created, based on
            the webhook's trigger configuration.

            Returns:
                function: Patched create method with webhook triggering logic
            """

            @api.model_create_multi
            def create(self, vals_list, **kw):
                """Patched create method to trigger webhooks on record creation.

                Args:
                    vals_list (list): List of value dicts for new records.
                    **kw: Additional keyword arguments.

                Returns:
                    recordset: The created records.
                """
                records = create.origin(self, vals_list, **kw)
                if (
                    webhooks := self.env["foreg.webhook"]
                    .sudo()
                    .search(
                        [
                            ("trigger", "in", ["on_create", "on_modification"]),
                            ("active", "=", True),
                            ("model_id.model", "=", self._name),
                        ]
                    )
                ):
                    webhooks.create_webhook_queue("create", records)
                return records

            return create

        def make_unlink():
            """Create a patched unlink method for webhook triggering.

            This function creates a patched version of the unlink method that
            automatically triggers webhooks when records are deleted, based on
            the webhook's trigger configuration.

            Returns:
                function: Patched unlink method with webhook triggering logic
            """

            def unlink(self, **kwargs):
                """Patched unlink method to trigger webhooks on record deletion.

                Args:
                    **kwargs: Additional keyword arguments.

                Returns:
                    bool: True if records were deleted.
                """
                if (
                    webhooks := self.env["foreg.webhook"]
                    .sudo()
                    .search(
                        [
                            ("trigger", "in", ["on_unlink", "on_modification"]),
                            ("active", "=", True),
                            ("model_id.model", "=", self._name),
                        ]
                    )
                ):
                    webhooks.create_webhook_queue("unlink", self)
                return unlink.origin(self, **kwargs)

            return unlink

        def make_write():
            """Create a patched write method for webhook triggering.

            This function creates a patched version of the write method that
            automatically triggers webhooks when records are updated, based on
            the webhook's trigger configuration.

            Returns:
                function: Patched write method with webhook triggering logic
            """

            def write(self, vals, **kwargs):
                """Patched write method to trigger webhooks on record update.

                Args:
                    vals (dict): Values to write to the records.
                    **kwargs: Additional keyword arguments.

                Returns:
                    bool: True if records were updated.
                """
                res = write.origin(self, vals, **kwargs)
                if (
                    webhooks := self.env["foreg.webhook"]
                    .sudo()
                    .search(
                        [
                            ("trigger", "in", ["on_write", "on_modification"]),
                            ("active", "=", True),
                            ("model_id.model", "=", self._name),
                        ]
                    )
                ):
                    webhooks.create_webhook_queue("write", self)
                return res

            return write

        patched_models = defaultdict(set)

        def patch(model, name, method):
            """Patch method `name` on `model` if not already patched.

            Args:
                model (Model): The Odoo model to patch.
                name (str): The method name to patch (e.g., 'create').
                method (function): The new method to set.
            """
            if model not in patched_models[name]:
                patched_models[name].add(model)
                ModelClass = model.env.registry[model._name]
                method.origin = getattr(ModelClass, name)
                setattr(ModelClass, name, method)

        for model in self.env.values():
            if isinstance(model, models.Model) and not isinstance(
                model, models.TransientModel
            ):
                patch(model, "create", make_create())
                patch(model, "unlink", make_unlink())
                patch(model, "write", make_write())
        _logger.info("Patched models for webhooks")

    def _unregister_hook(self):
        """Remove the patches installed by _register_hook().

        This method attempts to remove the patched 'create', 'write', and
        'unlink' methods from all models (except TransientModels). If a method
        cannot be unpatched, a warning is logged.
        """
        NAMES = ["create", "unlink", "write"]
        for Model in self.env.registry.values():
            if isinstance(Model, models.Model) and not isinstance(
                Model, models.TransientModel
            ):
                for name in NAMES:
                    try:
                        delattr(Model, name)
                    except AttributeError:
                        _logger.warning(
                            "Could not unpatch method %s on %s", name, Model._name
                        )

    def create_webhook_queue(self, method, records):
        """Create a webhook queue entry for the given method and records.

        This method is called by the patched model methods to enqueue webhook
        jobs for processing. It creates a new queue record for each webhook.

        Args:
            method (str): The method that triggered the webhook
                ('create', 'write', 'unlink').
            records (recordset): The records affected by the operation.
        """
        for record in self:
            _logger.info("Creating webhook queue for %s", record.display_name)
            record.queue_ids.sudo().create(
                {
                    "webhook_id": record.id,
                    "payload_json": [
                        {
                            "method": method,
                            "ids": records.ids,
                            "model": records._name,
                        }
                    ],
                    "state": "pending",
                }
            )
