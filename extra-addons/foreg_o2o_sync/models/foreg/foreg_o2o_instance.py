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

import base64
import json
import logging

import requests
from dateutil.relativedelta import relativedelta

from odoo import _, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class ForegO2oInstance(models.Model):
    """4EG O2O Instance for managing external Odoo connections.

    This model represents an external Odoo instance that can be synchronized
    with the current system. It handles authentication, API configuration,
    and various import/export operations for products, attributes, and
    other business data.
    """

    _name = "foreg.o2o.instance"
    _description = "4EG O2O Instance"
    _rec_name = "host"

    host = fields.Char(
        required=True,
        help="The host URL of the O2O instance to connect to",
    )
    username = fields.Char(
        required=False,
        help="Username for authentication with the O2O instance",
    )
    password = fields.Char(
        required=False,
        help="Password for authentication with the O2O instance",
    )
    access_token = fields.Char(
        readonly=True,
        copy=False,
        help="OAuth2 access token obtained after successful authentication",
    )
    expires_in = fields.Integer(
        readonly=True,
        copy=False,
        help="Number of seconds until the access token expires",
    )
    refresh_token = fields.Char(
        readonly=True,
        copy=False,
        help="OAuth2 refresh token used to obtain new access tokens",
    )
    refresh_expires_in = fields.Integer(
        readonly=True,
        copy=False,
        help="Number of seconds until the refresh token expires",
    )
    openapi_json_file = fields.Binary(
        string="OpenAPI JSON File",
        help="OpenAPI specification file defining the API endpoints and models",
    )
    openapi_filename = fields.Char(
        string="OpenAPI FileName",
        help="Name of the uploaded OpenAPI specification file",
    )
    request_ids = fields.One2many(
        comodel_name="foreg.o2o.request",
        inverse_name="instance_id",
        help="List of API requests associated with this O2O instance",
    )
    token_sync_datetime = fields.Datetime(
        readonly=True,
        help="Last date and time when the authentication tokens were synchronized",
    )

    is_import_product = fields.Boolean(
        string="Import Products",
        default=False,
        help="Enable to allow product import from O2O instance",
    )
    is_import_attributes = fields.Boolean(
        string="Import Attributes & Values",
        default=False,
        help="Enable to allow import of product attributes and their values",
    )
    is_export_product = fields.Boolean(
        string="Export Products",
        default=False,
        help="Enable to allow product export to O2O instance",
    )
    is_update_product = fields.Boolean(
        string="Update Products",
        default=False,
        help="Enable to allow updating existing products in O2O instance",
    )
    is_upload_product_img = fields.Boolean(
        string="Export Products Images",
        default=False,
        help="Enable to allow export of product images to O2O instance",
    )
    is_import_product_img = fields.Boolean(
        string="Import Products Images",
        default=False,
        help="Enable to allow import of product images from O2O instance",
    )
    is_import_price_items = fields.Boolean(
        string="Import Price Items",
        default=False,
        help="Enable to allow import of price items from O2O instance",
    )
    is_import_property = fields.Boolean(
        string="Import Properties",
        help="Enable to allow import of properties from O2O instance",
    )
    is_import_product_brand = fields.Boolean(
        string="Import Manufacturers (Product Brands)",
        help="Enable to allow import of manufacturer/brand information",
    )
    is_import_template = fields.Boolean(
        string="Import Templates",
        help="Enable to allow import of templates from O2O instance",
    )
    is_import_catalogs = fields.Boolean(
        string="Import Catalogs",
        help="Enable to allow import of catalogs from O2O instance",
    )
    product_tmpl_ids = fields.Many2many(
        comodel_name="product.template",
        column1="instrance_id",
        column2="product_template_id",
        relation="foreg_o2o_insatnce_product_template_rel",
        help="Product templates associated with this O2O instance",
    )
    is_import_order = fields.Boolean(
        string="Import Orders",
        default=False,
        help="Enable to allow import of orders from O2O instance",
    )
    orders_from_date = fields.Datetime(
        string="From",
        help="Start date for order import filter",
    )
    orders_to_date = fields.Datetime(
        string="To",
        help="End date for order import filter",
    )
    order_ids = fields.Char(
        "Order List",
        help=(
            "If you want to import specific orders, input "
            "List of Order's ID (SAAS) to this field (seperated by commas)"
        ),
    )
    active_cron_count = fields.Integer(
        default=0,
        help="Number of active cron jobs for this instance",
        compute="_compute_cron_count",
    )
    total_cron_count = fields.Integer(
        default=0,
        help="Total number of cron jobs for this instance",
        compute="_compute_cron_count",
    )
    fixed_value_ids = fields.One2many(
        comodel_name="foreg.o2o.instance.fixed.value",
        inverse_name="instance_id",
        context={"active_test": False},
        help="Fixed values for this instance",
    )

    def _compute_cron_count(self):
        """Compute the count of cron jobs for this instance.

        This method calculates the total number of cron jobs and active
        cron jobs associated with this O2O instance's requests.

        Example:
            >>> instance._compute_cron_count()
            >>> print(instance.active_cron_count, instance.total_cron_count)
        """
        ir_cron_env = self.env["ir.cron"].with_context(active_test=False)
        for instance in self.with_context(active_test=False):
            total_cron = ir_cron_env.search(
                [("o2o_request_id", "in", instance.request_ids.ids)]
            )
            instance.active_cron_count = len(total_cron.filtered("active"))
            instance.total_cron_count = len(total_cron)

    def action_authenticate(self):
        """Authenticate with the O2O instance to obtain access tokens.

        This method sends authentication credentials to the O2O instance
        and retrieves OAuth2 tokens for subsequent API operations.

        Returns:
            None: Updates the instance with authentication tokens

        Raises:
            ValidationError: When authentication fails or network errors occur

        Example:
            >>> instance.action_authenticate()
            >>> print(instance.access_token)
        """
        self.ensure_one()
        try:
            response = requests.post(
                f"{self.host}/api/auth/get_tokens",
                headers={"Content-Type": "text/html; charset=utf-8"},
                data=json.dumps(
                    {
                        "username": f"{self.username}",
                        "password": f"{self.password}",
                    }
                ),
                timeout=10,
            )
            if not response.ok:
                raise ValidationError(response.text)
        except Exception as e:
            raise ValidationError(
                _("Error found during authenticate:\n%s", str(e))
            ) from None
        response_data = response.json()
        self.write(
            {
                "access_token": response_data.get("access_token"),
                "expires_in": response_data.get("expires_in"),
                "refresh_token": response_data.get("refresh_token"),
                "refresh_expires_in": response_data.get("refresh_expires_in"),
                "token_sync_datetime": fields.Datetime.now(),
            }
        )

    def action_refresh_token(self):
        """Refresh the access token using the refresh token.

        This method uses the stored refresh token to obtain a new access
        token when the current one expires.

        Returns:
            None: Updates the instance with new access token

        Raises:
            ValidationError: When token refresh fails or network errors occur

        Example:
            >>> instance.action_refresh_token()
            >>> print(instance.access_token)
        """
        try:
            response = requests.post(
                f"{self.host}/api/auth/refresh_token",
                headers={"Content-Type": "text/html; charset=utf-8"},
                data=json.dumps(
                    {
                        "refresh_token": f"{self.refresh_token}",
                    }
                ),
                timeout=10,
            )
            if not response.ok:
                raise ValidationError(response.text)
        except Exception as e:
            raise ValidationError(
                _("Error found during refresh token:\n%s", str(e))
            ) from None
        response_data = response.json()
        self.write(
            {
                "access_token": response_data.get("access_token"),
                "expires_in": response_data.get("expires_in"),
                "token_sync_datetime": fields.Datetime.now(),
            }
        )

    def action_import_request(self):  # noqa: C901
        """Import API requests from OpenAPI specification file.

        This method parses the uploaded OpenAPI JSON file and automatically
        creates request configurations for different models and HTTP methods.
        It also sets up field mappings and handles recursive field relationships.

        Returns:
            None: Creates request records and field mappings

        Raises:
            ValidationError: When no OpenAPI file is uploaded

        Example:
            >>> instance.action_import_request()
        """
        self.ensure_one()

        def get_or_create_fields(field_name, request_model=None):
            """Create or retrieve field mappings for the request.

            This helper function creates field mapping records between
            source and target fields for O2O synchronization.

            Args:
                field_name (str): Name of the field to map
                request_model (str, optional): Model name for the field

            Returns:
                foreg.o2o.request.field: Created field mapping record
            """
            nonlocal request, request_method, imd_env
            request_model = request_model or request.model_id.model
            current_fields = request.get_fields().filtered(
                lambda x: x.model_id.model == request_model
            )
            if field_name in current_fields.mapped("source_field_name"):
                return
            request_model = im_env.search([("model", "=", request_model)], limit=1)
            vals = {
                "target_field_name": field_name,
                "source_field_name": field_name,
                "request_id": request.id,
                "request_method": request_method,
                "model_id": request_model.id,
            }
            field = imd_env.search(
                [("model_id", "=", request_model.id), ("name", "=", field_name)]
            )
            if field:
                target_field = field
                if field.name == "id":
                    saas_field = imd_env.search(
                        [("model_id", "=", request_model.id), ("name", "=", "saas_id")]
                    )
                    if saas_field:
                        target_field = saas_field
                        vals.update(target_field_name="saas_id")
                vals.update(source_field_id=field.id, target_field_id=target_field.id)
            return self.env["foreg.o2o.request.field"].create(vals)

        def get_or_create_recursion_fields(field_list=None, request_model=None):
            """Create recursive field mappings for related models.

            This helper function handles nested field mappings for relational
            fields (many2one, many2many, one2many) by recursively creating
            field mappings for related models.

            Args:
                field_list (list, optional): List of field names to process
                request_model (str, optional): Model name for the fields

            Returns:
                None: Creates recursive field mappings
            """
            nonlocal request, request_method, model_dict
            if field_list is None:
                field_list = model_dict.get(request.model_id.model, [])
            request_model = request_model or request.model_id.model
            request_model_env = self.env[request_model]
            for field_name in field_list:
                request_field = get_or_create_fields(field_name, request_model)
                if (
                    request_field
                    and request_field.source_field_type
                    in ["many2one", "many2many", "one2many"]
                    and request_field.source_field_id
                ):
                    target_model = request_model_env[
                        request_field.source_field_id.name
                    ]._name
                    get_or_create_recursion_fields(
                        model_dict.get(target_model, []), target_model
                    )

        if not self.openapi_json_file:
            raise ValidationError(
                _("You need to upload OpenAPI JSON File before importing request")
            )
        im_env = self.env["ir.model"]
        imd_env = self.env["ir.model.fields"]
        foreg_requets = self.request_ids
        try:
            json_content = base64.b64decode(self.openapi_json_file).decode()
            json_content = json.loads(json_content)
            for path in json_content.get("paths", []):
                path_list = path.split("/")
                if len(path_list) != 3:
                    continue
                model_name = path_list[2]
                model = im_env.search([("model", "=", model_name)], limit=1)
                if not model:
                    continue
                for method in ["read", "read_one", "create", "update", "call_method"]:
                    if foreg_requets.filtered(
                        lambda x, m=model, me=method: x.model_id == m and x.method == me
                    ):
                        continue
                    request = foreg_requets.create(
                        {
                            "instance_id": self.id,
                            "model_id": model.id,
                            "method": method,
                            "name": (
                                f"[{method.replace('_', ' ').title()}] "
                                f"Sync {model.name} from {self.host}"
                            ),
                        }
                    )
                    foreg_requets |= request
            model_dict = {}
            for model_name, model_properties in (
                json_content.get("components", {}).get("schemas", {}).items()
            ):
                model_name = model_name.replace("_", ".")
                model_dict[model_name] = [
                    field_name for field_name in model_properties.get("properties")
                ]

            for request in foreg_requets:
                request_method = request.method
                if request_method == "read_one":
                    request_method = "read"
                if request.method in ["call_method", "update", "read_one"]:
                    get_or_create_fields("id")
                if request.method in ("read", "read_one"):
                    get_or_create_recursion_fields()
                else:
                    for field in model_dict.get(request.model_id.model, []):
                        get_or_create_fields(field)

        except Exception as e:
            raise ValidationError(str(e)) from None

    def cron_refresh_token(self, seconds=-600):
        """Automatically refresh access tokens for all instances.

        This method is designed to be called by a cron job to refresh
        access tokens before they expire. It checks all instances and
        refreshes tokens that are close to expiration.

        Args:
            seconds (int, optional): Buffer time in seconds before expiration.
                Defaults to -600 (10 minutes before expiration).

        Example:
            >>> self.env['foreg.o2o.instance'].cron_refresh_token()
        """
        instances = self.search([("token_sync_datetime", "!=", False)])
        now = fields.Datetime.now()
        for instance in instances:
            to_sync_date = (
                instance.token_sync_datetime
                + relativedelta(seconds=instance.expires_in)
                + relativedelta(seconds=seconds)
            )
            if to_sync_date < now:
                _logger.info(f"Get new access token for instance {instance.host}")
                instance.action_authenticate()

    def action_view_cron(self):
        """Open view to display cron jobs for this instance.

        This method opens a window showing all scheduled actions (cron jobs)
        associated with this O2O instance's requests.

        Returns:
            dict: Action window definition for cron jobs

        Example:
            >>> action = instance.action_view_cron()
        """
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "ir.cron",
            "domain": [("o2o_request_id", "in", self.request_ids.ids)],
            "name": _("Scheduled Actions of Instance %s", self.host),
            "view_mode": "list,form",
            "context": {
                "search_default_all": 1,
            },
        }

    def get_fixed_value_dict(self):
        """Get fixed values dictionary for this instance.

        This method retrieves all active fixed values for this instance
        and organizes them by model and field for use in synchronization.

        Returns:
            dict: Dictionary organized by model and field with fixed values

        Example:
            >>> fixed_values = instance.get_fixed_value_dict()
            >>> print(fixed_values.get('res.partner', {}))
        """
        self.ensure_one()
        _logger.info(f"Get fixed value for instance {self.host}")
        fixed_values = self.fixed_value_ids.filtered("active")
        result = {}
        for fixed_value in fixed_values:
            value = fixed_value.convert_value()
            key = fixed_value.field_id.name
            model = fixed_value.model_id.model
            result.setdefault(model, {})
            result[model][key] = value
        return result
