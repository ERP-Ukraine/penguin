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

import ast
import base64
import json
import time
import traceback
from urllib.parse import urlencode, urljoin

import requests
from dateutil.relativedelta import relativedelta

from odoo import Command, _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import (
    DEFAULT_SERVER_DATE_FORMAT,
    DEFAULT_SERVER_DATETIME_FORMAT,
)

from ...tools.logger import Logger

DEFAULT_CONTEXT = """# Ex: result = {no_vat_validation: True}
# Common variables
#  - helper: foreg.o2o.helper env
#  - env: Odoo Environment on which the action is triggered
#  - uid: current user id
#  - user: current res.user
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


def field_kwarg(method, show_all=False):
    """Generate field keyword arguments for request field relationships.

    This helper function creates the standard keyword arguments for
    defining field relationships in O2O request models.

    Args:
        method (str): The request method to filter fields by
        show_all (bool, optional): Whether to show all fields including
            inactive ones. Defaults to False.

    Returns:
        dict: Keyword arguments for field relationship definition

    Example:
        >>> field_args = field_kwarg('read', show_all=True)
        >>> print(field_args)
    """
    return {
        "comodel_name": "foreg.o2o.request.field",
        "inverse_name": "request_id",
        "domain": [("request_method", "=", method)],
        "context": {"active_test": not show_all},
    }


class BytesEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles bytes
    objects by converting them to base64 strings."""

    def default(self, obj):
        """Handle bytes objects during JSON encoding.

        This method converts bytes objects to base64-encoded strings
        to ensure they can be properly serialized to JSON.

        Args:
            obj: Object to encode

        Returns:
            str: Base64-encoded string for bytes objects, or default
                handling for other types

        Example:
            >>> encoder = BytesEncoder()
            >>> result = encoder.default(b'binary_data')
        """
        if isinstance(obj, bytes):
            return base64.b64encode(obj).decode("utf-8")
        return super().default(obj)


class ForegO2oRequest(models.Model):
    """4EG O2O Request for managing API operations.

    This model represents API requests that can be executed against
    external Odoo instances. It handles various HTTP methods, field
    mapping, and response processing for O2O synchronization.
    """

    _name = "foreg.o2o.request"
    _description = "4EG O2O Request"
    _order = "sequence, id"

    sequence = fields.Integer(
        default=10,
        help="Sequence number for sorting requests",
    )
    url = fields.Char(
        string="URL",
        compute="_compute_url",
        store=True,
        help="The complete URL endpoint for the API request",
    )
    name = fields.Char(
        required=True,
        help="Name of the request for identification purposes",
    )
    method = fields.Selection(
        selection=[
            ("read", "Read"),
            ("read_one", "Read One"),
            ("create", "Create"),
            ("update", "Update"),
            ("call_method", "Call Method"),
            ("call_defined_method", "Call Defined Method"),
        ],
        required=True,
        default="read",
        help="Type of API request to be performed",
    )
    model_id = fields.Many2one(
        comodel_name="ir.model",
        ondelete="cascade",
        required=True,
        help="Odoo model on which the request will operate",
    )
    model = fields.Char(
        related="model_id.model",
        string="Model (Technical Name)",
        help="Technical name of the selected model",
    )
    instance_id = fields.Many2one(
        comodel_name="foreg.o2o.instance",
        required=True,
        ondelete="cascade",
        help="Target O2O instance for the API request",
    )
    access_token = fields.Char(
        related="instance_id.access_token",
        help="Authentication token for API access",
    )
    id_record = fields.Integer(
        string="ID Record",
        help="Specific record ID for single record operations",
    )
    read_filter = fields.Char(
        default="[]",
        help="Domain filter in Odoo format to filter records when reading",
    )
    read_offset = fields.Integer(
        default=0,
        help="Number of records to skip before starting to return results",
    )
    read_offset_step = fields.Integer(
        default=0,
        help=(
            "Increment value for offset after successful request. "
            "Used for pagination handling"
        ),
    )
    read_limit = fields.Integer(
        default=10,
        help="Maximum number of records to return in a single request",
    )
    read_order = fields.Char(
        default="id asc",
        help="Sorting criteria for the returned records (e.g., 'id asc', 'name desc')",
    )
    read_exclude_fields = fields.Char(
        default="['*']",
        help="List of fields to exclude from the response",
    )
    read_include_fields = fields.Char(
        default="[]",
        compute="_compute_read_include_fields",
        store=True,
        readonly=False,
        help="List of fields to specifically include in the response",
    )
    read_include_fields_display = fields.Char(
        compute="_compute_read_include_fields_display",
        compute_sudo=True,
        help="Formatted display of included fields for better readability",
    )
    values = fields.Text(
        default="{}",
        help="Values to use for create/update operations in JSON or Python dict format",
    )
    method_name = fields.Char(
        default="action_confirm",
        help="Name of the method to call when using call_method or call_defined_method",
    )
    timeout = fields.Integer(
        default=10,
        help="Maximum time in seconds to wait for API response",
    )
    log_ids = fields.One2many(
        comodel_name="foreg.o2o.request.log",
        inverse_name="request_id",
        help="History of request executions and their results",
    )

    field_ids = fields.One2many(
        comodel_name="foreg.o2o.request.field",
        inverse_name="request_id",
        context={"active_test": False},
        help="All fields configured for this request across all operations",
    )
    read_field_ids = fields.One2many(
        **field_kwarg("read"),
        help="Fields configured for reading operations",
    )
    read_field_display_ids = fields.One2many(
        **field_kwarg("read", show_all=True),
        help="Fields configured for reading operations",
    )

    update_field_ids = fields.One2many(
        **field_kwarg("update"),
        help="Fields configured for update operations",
    )
    update_field_display_ids = fields.One2many(
        **field_kwarg("update", show_all=True),
        help="Fields configured for update operations",
    )

    create_field_ids = fields.One2many(
        **field_kwarg("create"),
        help="Fields configured for create operations",
    )
    create_field_display_ids = fields.One2many(
        **field_kwarg("create", show_all=True),
        help="Fields configured for create operations",
    )

    call_method_field_ids = fields.One2many(
        **field_kwarg("call_method"),
        help="Fields configured for call_method operations",
    )
    call_method_field_display_ids = fields.One2many(
        **field_kwarg("call_method", show_all=True),
        help="Fields configured for call_method operations",
    )

    cron_ids = fields.One2many(
        comodel_name="ir.cron",
        inverse_name="o2o_request_id",
        context={"active_test": False},
        help=(
            "Scheduled jobs (crons) that automatically execute this O2O request at "
            "defined intervals. Shows both active and archived cron jobs."
        ),
    )
    server_action_id = fields.Many2one(
        comodel_name="ir.actions.server",
        help=(
            "Server action that will be triggered when executing this O2O request. "
            "Used to define custom logic and automation workflows."
        ),
    )
    mail_template_id = fields.Many2one(
        comodel_name="mail.template",
        string="Error Mail Template",
        domain="[('model', '=', 'foreg.o2o.request')]",
        help=(
            "Mail template to be used when an error occurs during the execution of "
            "this O2O request."
        ),
    )
    method_help_message = fields.Html(
        compute="_compute_method_help_message",
        help=(
            "Help message for the method used in this O2O request. "
            "Provides information about the method's parameters and usage."
        ),
    )
    last_sync_time = fields.Datetime(
        help="Timestamp of the last successful execution of this O2O request."
    )
    context = fields.Text(
        help="Context to use when creating or updating a record",
        default=DEFAULT_CONTEXT,
    )
    active = fields.Boolean(
        default=True,
        help="Indicates whether this O2O request is currently active and can be used.",
    )

    @api.depends("model_id", "instance_id.host", "method", "id_record")
    def _compute_url(self):
        """Compute the URL for the O2O request based on method and model.

        This method generates the appropriate API endpoint URL depending on the
        request method and model configuration. For call_defined_method, it uses
        the generic /api/method endpoint, otherwise it constructs the URL using
        the model name.

        Returns:
            None: Updates the url field directly on the record.
        """
        for rec in self:
            url = ""
            if rec.method == "call_defined_method":
                url = f"{rec.instance_id.host}/api/method"
            elif rec.model_id and rec.instance_id:
                url = f"{rec.instance_id.host}/api/{rec.model_id.model}"
            rec.url = url

    @api.depends(
        "model_id",
        "read_field_ids",
        "read_field_ids.active",
        "read_field_ids.model_id",
        "read_field_ids.source_field_name",
        "read_field_ids.source_field_type",
        "read_field_ids.apply_for_relation_model",
        "read_field_ids.related_field_ids",
        "read_field_ids.apply_for_root_model",
    )
    def _compute_read_include_fields(self):
        """Compute the read include fields for the O2O request.

        This method processes the read field configuration to generate a structured
        representation of fields to include when reading records. It handles nested
        relational fields and prevents circular references by maintaining an exclude
        list during recursion.

        Returns:
            None: Updates the read_include_fields field directly on the record.
        """

        def get_line_by_model(model_name, exclude_field_names=None, parent_field=None):
            """Get field lines for a specific model with recursion handling.

            Args:
                model_name (str): Name of the model to get fields for
                exclude_field_names (list, optional): List of field names to exclude
                parent_field (Model, optional): Parent field for relation handling

            Returns:
                list: List of field names or tuples for nested fields
            """
            result = []
            # Create a new list for this recursion level
            current_exclude_fields = (exclude_field_names or []).copy()

            lines = rec.read_field_ids.filtered(
                lambda x: x.model_name == model_name
                and (x.source_field_name or x.source_field_id.name)
                not in current_exclude_fields
            )
            if parent_field:
                lines = lines.filtered(
                    lambda x: x.apply_for_relation_model
                    or x in parent_field.related_field_ids
                )
            else:
                lines = lines.filtered(lambda x: x.apply_for_root_model)

            for line in lines:
                if line.source_field_type in ["many2many", "one2many", "many2one"]:
                    field_model_name = line.source_field_id.relation
                    source_field_name = (
                        line.source_field_name or line.source_field_id.name
                    )
                    # Pass a new copy of the exclude list to the recursive call
                    new_exclude_fields = current_exclude_fields + [source_field_name]
                    item = get_line_by_model(field_model_name, new_exclude_fields, line)
                    if item:
                        item = tuple(item)
                        if line.source_field_type.endswith("2many"):
                            item = [item]
                        result.append((source_field_name, item))
                    else:
                        result.append(source_field_name)
                else:
                    result.append(line.source_field_name or line.source_field_id.name)
            return result

        for rec in self:
            try:
                result = str(get_line_by_model(rec.model_id.model))
            except Exception:
                result = "[]"
            rec.read_include_fields = result

    @api.depends("read_include_fields")
    def _compute_read_include_fields_display(self):
        """Compute a formatted display version of the read include fields.

        This method converts the read_include_fields string representation into a
        human-readable JSON format for display purposes. If parsing fails, it
        falls back to the original string value.

        Returns:
            None: Updates the read_include_fields_display field directly on the record.
        """
        for rec in self:
            try:
                fields_list = ast.literal_eval(rec.read_include_fields)
                formatted = json.dumps(fields_list, indent=2)
                rec.read_include_fields_display = formatted
            except Exception:
                rec.read_include_fields_display = rec.read_include_fields

    @api.depends()
    def _compute_method_help_message(self):
        """Compute the help message for the selected method.

        This method provides contextual help information based on the selected
        request method. Currently supports help text for the call_defined_method
        which includes examples and available variables for Python code execution.

        Returns:
            None: Updates the method_help_message field directly on the record.
        """
        call_defined_method = """
        <p>Call a defined method on SAAS Instance</p>
        <p>Example: result = {"arg name": "arg value"}</p>
        <p>Common variables</p>
        <ul>
            <li>env: Odoo Environment on which the action is triggered</li>
            <li>uid: current user id</li>
            <li>user: current res.user</li>
            <li>records: current recordset, which trigger the action</li>
        </ul>
        <p>Python lib</p>
        <ul>
            <li>datetime</li>
            <li>json</li>
            <li>time</li>
            <li>dateutil</li>
            <li>timezone</li>
            <li>b64encode</li>
            <li>b64decode</li>
        </ul>
        <p>Odoo function</p>
        <ul>
            <li>Command</li>
            <li>float_compare</li>
            <li>UserError</li>
            <li>ValidationError</li>
            <li>log</li>
        </ul>
        """
        for rec in self:
            method_help_message = False
            if rec.method == "call_defined_method":
                method_help_message = call_defined_method
            rec.method_help_message = method_help_message

    @api.onchange("method", "model_id", "instance_id", "method_name")
    def _onchange_method_model_id_instance_id(self):
        """Update the name field when method, model, instance, or method name changes.

        This method automatically generates a descriptive name for the O2O request
        based on the selected method and model. For call_defined_method, it uses
        the method_name field instead of the model name.

        Returns:
            None: Updates the name field directly on the record.
        """
        self.name = (
            f"[{self.method.replace('_', ' ').title()}] " f"Sync {self.model_id.name}"
        )
        if self.method == "call_defined_method":
            self.name = (
                f"[{self.method.replace('_', ' ').title()}] " f"{self.method_name}"
            )

    def copy(self, default=None):
        """Create a copy of the O2O request record with its associated fields.

        This method overrides the default copy behavior to ensure that all
        related field configurations are also copied to the new record.

        Args:
            default (dict, optional): Default values to override in the copy.
                Defaults to None.

        Returns:
            Model: The newly created copy of the O2O request record.
        """
        # also copy the fields to the new record
        new_record = super().copy(default)
        for field in self.field_ids:
            field.copy(default={"request_id": new_record.id})
        return new_record

    def action_send_request(self, **kwargs):  # noqa: C901
        """Send the O2O request to the configured endpoint.

        This method executes the O2O request based on the configured method and
        parameters. It handles different HTTP methods (GET, POST, PUT) and
        processes the response accordingly.

        Args:
            **kwargs: Additional parameters to override default values:
                - id_record: Record ID for read_one, update, call_method
                - values: Data to send for create, update, call_method
                - read_filter: Filter for read operations
                - read_offset: Offset for pagination
                - read_limit: Limit for pagination
                - read_order: Ordering for read operations
                - read_exclude_fields: Fields to exclude
                - read_include_fields: Fields to include
                - method_name: Method name for call_method
                - include_read_filter: Whether to combine with field filter
                - return_request_log: Return log instead of notification
                - raise_if_fail: Raise exception on failure

        Returns:
            Model or dict: Request log record or notification action depending on kwargs
        """

        def get_value(key):
            """Get value from kwargs or fallback to record field.

            Args:
                key (str): Key to retrieve value for

            Returns:
                any: Value from kwargs or record field
            """
            return kwargs.get(key) or self[key]

        def get_value_with_ast(key):
            """Get value and evaluate string literals if needed.

            Args:
                key (str): Key to retrieve value for

            Returns:
                any: Evaluated value or original value
            """
            value = get_value(key)
            if isinstance(value, str):
                value = ast.literal_eval(value)
            return value

        def get_combined_read_filter():
            """Combine kwargs read_filter with
            field read_filter using AND operator."""
            field_filter = (
                ast.literal_eval(self.read_filter) if self.read_filter else []
            )
            read_filter = get_value_with_ast("read_filter")
            if kwargs.get("include_read_filter") and kwargs.get("read_filter"):
                read_filter = ["&"] + field_filter + read_filter
            return read_filter

        self.ensure_one()
        log = Logger()
        start_time = time.time()
        log.title(f"Send request {self.url}")
        log.info("Compute request kwargs")
        request_kwargs = {
            "headers": {
                "Content-Type": "text/html; charset=utf-8",
                "Access-Token": self.access_token,
            },
            "timeout": self.timeout,
        }
        data = None
        url_params = {}
        url = self.url
        state = "pass"
        response_json = {}
        if self.method in ("read_one", "update", "call_method"):
            url = urljoin(url + "/", str(get_value("id_record")))
        try:
            if self.method == "read":
                url_params = {
                    "filters": get_combined_read_filter(),
                    "offset": get_value("read_offset"),
                    "limit": get_value("read_limit"),
                    "order": get_value("read_order"),
                    "exclude_fields": get_value_with_ast("read_exclude_fields"),
                    "include_fields": get_value_with_ast("read_include_fields"),
                }
            elif self.method == "read_one":
                url_params = {
                    "exclude_fields": get_value_with_ast("read_exclude_fields"),
                    "include_fields": get_value_with_ast("read_include_fields"),
                }
            elif self.method == "call_defined_method":
                url = urljoin(url + "/", str(get_value("method_name")))
                data = get_value("values")
                if isinstance(data, str):
                    data = self.compute_values_python_code(
                        {"records": self.env[self.model_id.model]}
                    )
            elif self.method in ("create", "update", "call_method"):
                data = get_value_with_ast("values")
                if self.method == "call_method":
                    url = urljoin(url + "/", str(get_value("method_name")))
                elif self.method == "create":
                    url_params = {
                        "__domain_fields__": self.create_field_ids.filtered(
                            "is_domain_field"
                        ).mapped("source_field_name")
                    }
                    if not data and kwargs.get("record"):
                        data = self.convert_record_to_vals(kwargs.get("record"))
            if self.context:
                request_context = self.env["foreg.o2o.helper"].compute_python_code(
                    {"result": {}},
                    self.context,
                )
                url_params.update({"__context__": request_context})

            if url_params:
                url = urljoin(url, "?" + urlencode(url_params))

            if data:
                request_kwargs.update(data=json.dumps(data, cls=BytesEncoder))
            request_kwargs.update(url=url)
            request_kwargs["method"] = {
                "read": "get",
                "read_one": "get",
                "create": "post",
                "update": "put",
                "call_method": "put",
                "call_defined_method": "post",
            }.get(self.method)

            for key, value in request_kwargs.items():
                log.info(f"- {key}: {value}")

            response = requests.request(  # pylint: disable=E8106
                **request_kwargs,
            )
            if not response.ok:
                state = "fail"
                log.error("Request failed")
                # Try to get error description from JSON response if available
                try:
                    error_json = response.json()
                    if error_json.get("error_descrip"):
                        log.error(error_json.get("error_descrip"))
                except Exception:
                    # If response is not valid JSON, use the raw text
                    log.error(response.text)
            try:
                response_json = response.json()
            except Exception:
                response_json = {"data": response.text}

        except Exception as e:
            state = "fail"
            log.error(traceback.format_exc())
            response_json["error"] = str(e)

        log.info(f"request done with state {state}")
        request_log = self.log_ids.sudo().create(
            {
                "request_id": self.id,
                "state": state,
                "read_filter": (
                    str(get_combined_read_filter()) if self.method == "read" else False
                ),
                "model": self.model,
            }
        )
        if self.method in ["read", "read_one"] and state == "pass":
            try:
                with self.env.cr.savepoint():
                    if self.method == "read":
                        data = response_json.get("results")
                    else:
                        data = [response_json]
                    self.with_context(
                        execute_time=start_time
                    ).create_or_update_record_from_response(
                        data,
                        log,
                        request_log,
                    )
            except Exception as e:
                state = "fail"
                response_json["error"] = str(e)
                log.error(traceback.format_exc())
        elif self.method == "create" and state == "pass" and kwargs.get("record"):
            self.set_saas_id_to_record(
                kwargs.get("record"),
                response_json,
                log,
                request_log,
            )

        if kwargs.get("raise_if_fail") and state == "fail":
            if response_json.get("error") and response_json.get("error_descrip"):
                raise ValidationError(
                    f"{response_json['error']}\n{response_json['error_descrip']}"
                )
            else:
                raise ValidationError(str(response_json))
        elif self.method == "read" and state == "pass":
            log.info(f"Increase offset by {self.read_offset_step}")
            self.read_offset += self.read_offset_step

        if state == "fail" and self.mail_template_id:
            self.mail_template_id.send_mail(self.id)

        request_log.write(
            {
                "logs": log.get_logs(),
                "request_kwargs_json": request_kwargs,
                "response_json": response_json,
                "execution_time": time.time() - start_time,
                "state": state,
            }
        )
        if state == "pass":
            self.last_sync_time = fields.Datetime.now()
        if kwargs.get("return_response_data"):
            return response_json
        if kwargs.get("return_request_log"):
            return request_log
        return request_log.action_display_notification()

    def create_or_update_record_from_response(  # noqa: C901
        self,
        response_json,
        log,
        request_log,
        model_name=None,
        parent_field=None,
        use_command=False,
        record_ids_vals=None,
    ):
        """Create or update records from the API response data.

        This method processes the response JSON data and creates new records or
        updates existing ones based on the field mapping configuration. It handles
        nested relational fields recursively and maintains referential integrity.

        Args:
            response_json (list): List of record data dictionaries from API response
            log (Logger): Logger instance for tracking operations
            request_log (Model): Request log record for audit trail
            model_name (str, optional): Target model name. Defaults to request model
            parent_field (Model, optional): Parent field for relation handling
            use_command (bool, optional): Whether to use Command objects for relations
            record_ids_vals (list, optional): Accumulator for record IDs and values

        Returns:
            list or Model: List of created/updated records or single record ID
        """
        self.ensure_one()
        model_name = model_name or self.model_id.model
        log.info(f"[{model_name}] create or update record for model")

        # Only initialize at the top-level call
        is_top_level = False
        if record_ids_vals is None:
            record_ids_vals = []
            is_top_level = True

        related_fields = self.read_field_ids.filtered(
            lambda x: x.model_name == model_name
        )
        if parent_field:
            related_fields = related_fields.filtered(
                lambda x: x in parent_field.related_field_ids
                or x.apply_for_relation_model
            )
        else:
            related_fields = related_fields.filtered(lambda x: x.apply_for_root_model)

        map_field_dict = related_fields.get_map_field_dict().get(model_name, {})
        domain_fields = related_fields.get_domain_field_dict().get(model_name, [])
        result = model_env = self.env[model_name].sudo()
        if use_command:
            result = []

        for values in response_json:
            new_values = {}
            log.info(values)
            for key, value in values.items():
                if key not in map_field_dict:
                    log.warning(
                        f"[{model_name}] field {key} not found in map_field_dict"
                    )
                    continue
                new_key = map_field_dict.get(key, key)
                new_value = value
                field_type = model_env._fields[new_key].type
                field = related_fields.filtered(
                    lambda x, nk=new_key: x.target_field_name == nk
                )

                if (
                    field_type in ["many2one", "one2many", "many2many"]
                    and new_value
                    and (isinstance(new_value, list) or isinstance(new_value, dict))
                ):
                    field_model = model_env._fields[new_key].comodel_name
                    if field_type == "many2one":
                        new_value = self.create_or_update_record_from_response(
                            [new_value],
                            log,
                            request_log,
                            field_model,
                            field,
                            False,
                            record_ids_vals,
                        )
                        new_value = new_value.id
                    elif field_type == "one2many":
                        new_value = self.create_or_update_record_from_response(
                            new_value,
                            log,
                            request_log,
                            field_model,
                            field,
                            True,
                            record_ids_vals,
                        )
                        if new_value == []:
                            continue
                    else:  # many2many
                        new_value = self.create_or_update_record_from_response(
                            new_value,
                            log,
                            request_log,
                            field_model,
                            field,
                            False,
                            record_ids_vals,
                        )
                        new_value = [Command.set(new_value.ids)]

                log.info(f"[{model_name}][{field_type}] {new_key}: {new_value}")
                new_values.update({new_key: new_value})

            domain = [
                (key, "=", value)
                for key, value in new_values.items()
                if key in domain_fields
            ]
            request_context = {}
            if self.context:
                request_context = self.env["foreg.o2o.helper"].compute_python_code(
                    {"result": {}},
                    self.context,
                )
            record = model_env = model_env.with_context(**request_context)
            if domain:
                log.info(f"[{model_name}] domain: {domain}")
                record = self._get_existing_record(
                    model_env.with_context(active_test=False), domain
                )
                if not record:
                    log.info(f"[{model_name}] create a new record")
                    method = "create"
                else:
                    if len(record) > 1:
                        log.warning(f"[{model_name}] multiple records found")
                        record = record[0]
                    log.info(f"[{model_name}] update old record {record}")
                    method = "write"
            else:
                log.info(f"[{model_name}] create a new record")
                method = "create"

            # Handle fixed values process
            new_values = self.instance_id.fixed_value_ids.filtered(
                "active"
            ).handle_fixed_values(new_values, record, log)

            for field in self.read_field_ids.filtered(
                lambda x: x.model_name == model_name
            ):
                # Skip fields that shouldn't be used in create/write operations
                if (
                    (method == "create" and not field.use_in_create)
                    or (method == "write" and not field.use_in_write)
                ) and field.target_field_name in new_values:
                    new_values.pop(field.target_field_name, None)

            if record:
                # Filter the new values to only include the values
                # that differ from the record values
                new_values = self.filter_actual_new_values(record, new_values)

            if new_values:
                if use_command:
                    if method == "create":
                        result.append(Command.create(new_values))
                    elif method == "write":
                        result.append(Command.update(record.id, new_values))
                else:
                    method_res = getattr(record, method)(new_values)
                    record = (
                        method_res
                        if isinstance(method_res, models.BaseModel)
                        else record
                    )
                    result |= record
            else:
                log.warning(f"[{model_name}] no values to create/update")
                if record and not use_command:
                    result |= record
                continue
            # Always append to the shared record_ids_data list
            record_ids_vals.append(
                {
                    "log_id": request_log.id,
                    "method_applied": method,
                    "res_model": model_name,
                    "res_id": record.id,
                    "process_values_json": new_values,
                }
            )
        # Only batch create at the top-level call
        if is_top_level and record_ids_vals:
            request_log.record_ids.sudo().create(record_ids_vals)
        return result

    # TODO: Uncomment this when we have a way to invalidate the cache
    # @ormcache(
    #     "model_env._name",
    #     "tuple(domain)",
    #     "self.env.context.get('execute_time')",
    # )
    def _get_existing_record(self, model_env, domain):
        """Search for existing records based on the given domain.

        This method searches for existing records in the specified model using
        the provided domain criteria. It only fetches essential fields (id and
        display_name) for performance optimization.

        Args:
            model_env (Model): The model environment to search in
            domain (list): Search domain criteria

        Returns:
            Recordset: Found records with id and display_name fields
        """
        return model_env.search_fetch(
            domain,
            ["id", "display_name"],
        )

    def set_saas_id_to_record(self, record, response_json, log, request_log):
        """Set the SAAS ID from response to the local record.

        This method extracts the SAAS ID from the response JSON and sets it to
        the corresponding local record. It supports both 'saas_id' and 'x_saas_id'
        field names and creates an audit log entry for the operation.

        Args:
            record (Model): The local record to update with SAAS ID
            response_json (dict): Response data containing the SAAS ID
            log (Logger): Logger instance for tracking operations
            request_log (Model): Request log record for audit trail

        Returns:
            None: Updates the record and creates audit log entry
        """
        if not isinstance(response_json, dict):
            return
        log.info(f"[{record._name}] trying to set saas_id to record")
        saas_id = response_json.get("id")
        saas_field = ""
        if "saas_id" in record._fields:
            saas_field = "saas_id"
        elif "x_saas_id" in record._fields:
            saas_field = "x_saas_id"
        if saas_field and saas_id:
            log.info(
                f"[{record._name}] setting saas_id "
                f"to {saas_field} for record with id {record.id}"
            )
            record.write({saas_field: saas_id})
            request_log.record_ids.sudo().create(
                {
                    "log_id": request_log.id,
                    "method_applied": "write",
                    "res_model": record._name,
                    "res_id": record.id,
                    "process_values_json": {saas_field: saas_id},
                }
            )

    def filter_actual_new_values(self, record, values):
        """Filter the new values to only include
        the values that differ from the record values.

        Args:
            record (Model): Any Odoo record
            values (dict): Dictionary of field values to check

        Returns:
            dict: Dictionary containing only the values that differ from the record
        """
        actual_values = {}
        current_values = record.read(list(values.keys()), load="no_name_get")[0]
        for field_name, value in values.items():
            if field_name not in current_values:
                actual_values[field_name] = value
                continue

            current_value = current_values.get(field_name)
            field = record._fields[field_name]

            if field.type in ["many2many", "one2many"]:
                # Skip relational fields that use Commands
                current_value = [Command.set(current_value)] if current_value else []
            if field.type == "datetime" and current_value:
                current_value = current_value.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
            elif field.type == "date" and current_value:
                current_value = current_value.strftime(DEFAULT_SERVER_DATE_FORMAT)

            # Only include values that are different
            if current_value != value and (current_value or value):
                actual_values[field_name] = value

        return actual_values

    def convert_record_to_vals(self, record):
        """Convert an Odoo record to a dictionary of values for API requests.

        This method processes the configured fields and converts the record data
        to the format expected by the API. It handles field context and value
        conversion for different field types.

        Args:
            record (Model): The Odoo record to convert

        Returns:
            dict: Dictionary containing field values mapped to source field names

        Raises:
            ValidationError: When there's an error parsing the field context
        """
        self.ensure_one()
        vals = {}
        for field in self.get_fields().filtered(
            lambda x: x.model_id == x.request_id.model_id
        ):
            if field.context:
                try:
                    record = record.with_context(**ast.literal_eval(field.context))
                except Exception as e:
                    raise ValidationError(
                        _("Error during passing context: %s", str(e))
                    ) from None
            value = self.convert_field_value_to_vals(record, field.target_field_name)
            vals[field.source_field_name] = value
        return vals

    def action_create_server_action(self):
        """Create or update a server action for this O2O request.

        This method creates a new server action or updates an existing one that
        can be triggered from the UI. The server action contains the generated
        Python code to execute the O2O request.

        Returns:
            None: Creates/updates the server action and links it to the request
        """
        server_action_env = self.env["ir.actions.server"]
        self.ensure_one()
        vals = {
            "name": self.display_name,
            "model_id": self.model_id.id,
            "state": "code",
            "binding_view_types": "list,form",
            "code": getattr(self, f"generate_server_action_code_{self.method}")(),
            "o2o_request_id": self.id,
        }
        existing_record = server_action_env.search(
            [
                ("o2o_request_id", "=", self.id),
            ]
        )
        if existing_record:
            existing_record.unlink_action()
            existing_record.write(vals)
        else:
            existing_record = existing_record.create(vals)
        existing_record.create_action()
        self.server_action_id = existing_record

    def action_create_cron(self):
        """Create a scheduled action (cron) for this O2O request.

        This method creates a new scheduled action that will automatically execute
        the O2O request on a daily basis. The cron is created as inactive by
        default and can be activated manually.

        Returns:
            dict: Action to open the created cron record in a new window
        """
        self.ensure_one()
        code = f"request = env['foreg.o2o.request'].browse({self.id})\n"
        code += "request.action_send_request(raise_if_fail=True)\n"
        request_cron = self.env["ir.cron"].create(
            {
                "name": f"{self.instance_id.host}: {self.display_name}",
                "o2o_request_id": self.id,
                "model_id": self.env.ref("foreg_o2o_sync.model_foreg_o2o_request").id,
                "state": "code",
                "interval_number": 1,
                "interval_type": "days",
                "user_id": self.env.user.id,
                "nextcall": fields.Datetime.now() + relativedelta(days=1),
                "code": code,
                "active": False,
            }
        )
        return {
            "name": _("Scheduled Action"),
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "ir.cron",
            "res_id": request_cron.id,
            "target": "new",
        }

    def generate_server_action_code_update(self):
        """Generate Python code for server action update method.

        This method generates the Python code that will be executed by the server
        action when updating records. The code converts the record to values and
        sends an update request.

        Returns:
            str: Python code string for the server action
        """
        return (
            f"for record in records:"
            f"\n\trequest = env['foreg.o2o.request'].browse({self.id})"
            f"\n\tvals = request.convert_record_to_vals(record)"
            f"\n\taction = request.action_send_request("
            f"\n\t\tid_record=vals.get('id'), values=str(vals)"
            f"\n\t)"
        )

    def generate_server_action_code_create(self):
        """Generate Python code for server action create method.

        This method generates the Python code that will be executed by the server
        action when creating records. The code sends a create request with the
        record data.

        Returns:
            str: Python code string for the server action
        """
        return (
            f"for record in records:"
            f"\n\trequest = env['foreg.o2o.request'].browse({self.id})"
            f"\n\taction = request.action_send_request(values='{{}}', record=record)"
        )

    def generate_server_action_code_read_one(self):
        """Generate Python code for server action read_one method.

        This method generates the Python code that will be executed by the server
        action when reading a single record. The code converts the record to
        values and sends a read_one request.

        Returns:
            str: Python code string for the server action
        """
        return (
            f"for record in records:"
            f"\n\trequest = env['foreg.o2o.request'].browse({self.id})"
            f"\n\tvals = request.convert_record_to_vals(record)"
            f"\n\taction = request.action_send_request(id_record=vals.get('id'))"
        )

    def generate_server_action_code_call_method(self):
        """Generate Python code for server action call_method.

        This method generates the Python code for calling a method on the
        remote instance. It reuses the update code generation logic.

        Returns:
            str: Python code string for the server action
        """
        return self.generate_server_action_code_update()

    def generate_server_action_code_call_defined_method(self):
        """Generate Python code for server action call_defined_method.

        This method generates the Python code for calling a user-defined method
        on the remote instance. The code computes values using Python code and
        sends the request.

        Returns:
            str: Python code string for the server action
        """
        return (
            f"if records:"
            f"\n\trequest = env['foreg.o2o.request'].browse({self.id})"
            "\n\tvals = request.compute_values_python_code({'records': records})"
            f"\n\taction = request.action_send_request(values=vals)"
        )

    def get_fields(self):
        """Get the appropriate field configuration based on the request method.

        This method returns the correct field configuration recordset based on
        the current request method. Different methods use different field
        configurations (create, read, update, etc.).

        Returns:
            Recordset: The appropriate field configuration for the current method
        """
        self.ensure_one()
        field_name = {
            "create": "create_field_ids",
            "read": "read_field_ids",
            "read_one": "read_field_ids",
            "update": "update_field_ids",
            "call_method": "call_method_field_ids",
        }.get(self.method)
        return self[field_name]

    def compute_values_python_code(self, localdict):
        """Execute Python code to compute values for the request.

        This method uses the foreg.o2o.helper to execute Python code stored in
        the values field. The code can access variables from the localdict
        parameter.

        Args:
            localdict (dict): Dictionary containing local variables for code execution

        Returns:
            any: Result of the Python code execution
        """
        self.ensure_one()
        return self.env["foreg.o2o.helper"].compute_python_code(localdict, self.values)

    def convert_field_value_to_vals(self, record, field_name):
        """Convert a single field value to the format expected by the API.

        This method handles the conversion of individual field values from Odoo
        format to API format. It handles special cases for relational fields,
        datetime fields, and date fields.

        Args:
            record (Model): The Odoo record containing the field
            field_name (str): Name of the field to convert

        Returns:
            any: Converted field value suitable for API transmission

        Raises:
            ValidationError: When relational fields lack required SAAS ID fields
        """
        self.ensure_one()
        value = record[field_name]
        field_type = record._fields[field_name].type
        if field_type in ["many2one", "one2many", "many2many"]:
            comodel = record._fields[field_name].comodel_name
            comodel_fields = self.env[comodel]._fields
            saas_field = False
            if "saas_id" in comodel_fields:
                saas_field = "saas_id"
            elif "x_saas_id" in comodel_fields:
                saas_field = "x_saas_id"
            else:
                raise ValidationError(
                    _(
                        "Error during converting relation field "
                        "%(field_name)s because model %(comodel)s"
                        " does not have saas_id or x_saas_id",
                        field_name=field_name,
                        comodel=comodel,
                    )
                )
            missing_saas_id_records = value.filtered(lambda x: not x[saas_field])
            if missing_saas_id_records:
                raise ValidationError(
                    _(
                        "Error during converting relation field "
                        "%(field_name)s because some records "
                        "do not have %(saas_field)s: %(records)s",
                        field_name=field_name,
                        saas_field=saas_field,
                        records=str(missing_saas_id_records.ids),
                    )
                )
            if field_type == "many2one":
                return value[saas_field]
            else:  # many2many, one2many
                return [Command.set(value.mapped(saas_field))]
        if field_type == "datetime":
            return value.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        if field_type == "date":
            return value.strftime(DEFAULT_SERVER_DATE_FORMAT)
        return value
