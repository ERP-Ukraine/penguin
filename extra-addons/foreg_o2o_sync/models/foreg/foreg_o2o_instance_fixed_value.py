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
from datetime import datetime

from odoo import Command, _, api, fields, models
from odoo.exceptions import ValidationError

from ...tools.logger import Logger


class ForegO2oInstanceFixedValue(models.Model):
    """4EG O2O Instance Fixed Value for field synchronization.

    This model defines fixed values that will be applied to specific fields
    during O2O synchronization operations. It allows setting default or
    constant values for fields across different models and instances.
    """

    _name = "foreg.o2o.instance.fixed.value"
    _description = "4EG O2O Instance Fixed Value"

    instance_id = fields.Many2one(
        comodel_name="foreg.o2o.instance",
        required=True,
        ondelete="cascade",
        help="The O2O instance this fixed value belongs to",
    )
    model_id = fields.Many2one(
        comodel_name="ir.model",
        required=True,
        ondelete="cascade",
        help="The Odoo model where this fixed value will be applied",
    )
    field_id = fields.Many2one(
        domain="[('model_id', '=', model_id)]",
        comodel_name="ir.model.fields",
        required=True,
        ondelete="cascade",
        help=(
            "The specific field within the model" " that will receive this fixed value"
        ),
    )
    value = fields.Char(
        required=True,
        help=(
            "The fixed value that will be assigned to the specified field "
            "during O2O synchronization"
        ),
    )
    active = fields.Boolean(
        default=True,
        help=(
            "Whether this fixed value is currently active and will be applied "
            "during O2O synchronization"
        ),
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        ondelete="cascade",
        help="The Odoo Company where this fixed value will be applied",
    )
    team_id = fields.Many2one(
        comodel_name="crm.team",
        ondelete="cascade",
        help="The Odoo CRM Team where this fixed value will be applied",
    )

    @api.constrains("instance_id", "model_id", "field_id", "company_id", "team_id")
    def _check_unique_fixed_value(self):
        """Ensure unique fixed values per instance, model, and field combination.

        This constraint prevents duplicate fixed values for the same
        instance, model, and field combination.

        Raises:
            ValidationError: When a duplicate fixed value is detected

        Example:
            >>> fixed_value = self.create({
            ...     'instance_id': instance.id,
            ...     'model_id': model.id,
            ...     'field_id': field.id,
            ...     'value': 'default_value'
            ... })
        """
        for record in self:
            domain = [
                ("instance_id", "=", record.instance_id.id),
                ("model_id", "=", record.model_id.id),
                ("field_id", "=", record.field_id.id),
                ("company_id", "=", record.company_id.id),
                ("team_id", "=", record.team_id.id),
            ]
            existing_record = self.search_count(domain)
            if existing_record > 1:
                raise ValidationError(
                    _(
                        "A fixed value already exists for instance "
                        '"%(instance_name)s", model "%(model_name)s"'
                        ', and field "%(field_name)s", with the same '
                        'company "%(company)s" and team "%(team)s".',
                        instance_name=record.instance_id.host,
                        model_name=record.model_id.name,
                        field_name=record.field_id.field_description,
                        company=record.company_id.name,
                        team=record.team_id.name,
                    )
                )

    @api.constrains("instance_id", "model_id", "field_id", "value")
    def _check_value(self):
        """Validate that the value can be converted to the field's type.

        This constraint ensures that the stored value can be properly
        converted to the target field's data type during synchronization.

        Raises:
            ValidationError: When the value cannot be converted to the
                required field type

        Example:
            >>> fixed_value = self.create({
            ...     'instance_id': instance.id,
            ...     'model_id': model.id,
            ...     'field_id': field.id,
            ...     'value': '123'  # Must be convertible to field type
            ... })
        """
        for record in self:
            try:
                record.convert_value()
            except Exception as e:
                raise ValidationError(
                    _(
                        "Can not convert value of field %(field)s to type %(type)s"
                        "\n%(error)s",
                        field=record.field_id.field_description,
                        type=record.field_id.ttype,
                        error=str(e),
                    )
                ) from None

    def convert_value(self):
        """Convert the stored string value to the appropriate field type.

        This method converts the stored string value to the target field's
        data type for use during synchronization operations.

        Returns:
            any: Converted value in the appropriate data type

        Raises:
            ValidationError: When the value cannot be converted to the
                required field type

        Example:
            >>> fixed_value = self.browse(1)
            >>> converted_value = fixed_value.convert_value()
            >>> print(type(converted_value))
        """
        self.ensure_one()
        result = self.value
        if self.field_id.ttype in ["many2one", "integer", "many2one_reference"]:
            result = int(self.value)
        elif self.field_id.ttype in ["float", "monetary"]:
            result = float(self.value)
        elif self.field_id.ttype == "boolean":
            if self.value not in ["True", "False"]:
                raise ValidationError(_("Value must be True or False"))
            result = self.value == "True"
        elif self.field_id.ttype == "date":
            result = datetime.strptime(self.value, "%Y-%m-%d")
        elif self.field_id.ttype == "datetime":
            result = datetime.strptime(self.value, "%Y-%m-%d %H:%M:%S")
        elif self.field_id.ttype in [
            "json",
            "properties",
            "properties_definition",
        ]:
            result = json.loads(self.value)
        elif self.field_id.ttype in ["many2many", "one2many"]:
            result = [Command.set(json.loads(self.value))]
        return result

    def _extract_field_id(self, record, values, field_name, alt_field_name=None):
        """Helper method to extract ID values from either values or record"""
        if field_name in record._fields:
            field_to_use = field_name
        elif alt_field_name in record._fields:
            field_to_use = alt_field_name
        else:
            return False

        # Try to get value from values
        value = values.get(field_to_use)

        # If not found in values, try to get from record
        if not value:
            value = record[field_to_use].id
        return value

    def handle_fixed_values(self, values, record, log=None):
        """Apply fixed values to record values based on configured rules.

        This method processes all fixed value configurations that match the
        given record's model and applies them to the values dictionary.
        Fixed values are filtered by company and team matching rules.

        Args:
            values (dict): Dictionary of field values to be updated with
                fixed values
            record (Model): Odoo record instance to extract context info
                from (model name, company_id, team_id)
            log (Logger, optional): Logger instance for tracking applied
                fixed values. Defaults to None (creates new Logger).

        Returns:
            dict: Updated values dictionary with applied fixed values

        Example:
            >>> fixed_values = self.browse([1, 2, 3])
            >>> values = {'name': 'Test Record'}
            >>> record = self.env['sale.order'].browse(1)
            >>> updated_values = fixed_values.handle_fixed_values(
            ...     values, record
            ... )
        """
        model_name = record._name
        company_id = self._extract_field_id(
            record, values, "company_id", "x_company_id"
        )
        team_id = self._extract_field_id(record, values, "team_id", "x_team_id")
        log = log or Logger()
        info_msg = "[%(model_name)s][%(field)s] use fixed value: %(value)s"

        updated_field_list = []

        for fixed_val_rec in self.filtered(lambda x: x.model_id.model == model_name):
            field_name = fixed_val_rec.field_id.name
            value = fixed_val_rec.value
            if field_name in updated_field_list:
                continue

            company_match = (
                not fixed_val_rec.company_id
                or company_id == fixed_val_rec.company_id.id
            )
            team_match = (
                not fixed_val_rec.team_id or team_id == fixed_val_rec.team_id.id
            )

            if company_match and team_match:
                values[field_name] = value
                log.info(
                    info_msg
                    % {"model_name": model_name, "field": field_name, "value": value}
                )
                updated_field_list.append(field_name)

        return values
