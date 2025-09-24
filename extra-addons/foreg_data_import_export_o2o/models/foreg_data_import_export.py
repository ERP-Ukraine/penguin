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

from odoo import _, fields, models
from odoo.exceptions import UserError


class ForegDataImportExport(models.Model):
    _inherit = "foreg.data.import.export"

    o2o_instance_id = fields.Many2one(
        "foreg.o2o.instance",
        string="O2O Instance",
        help="O2O Instance to use for the import/export",
    )

    model = fields.Selection(
        selection_add=[
            ("foreg.o2o.instance", "O2O Instance"),
        ],
        ondelete={"foreg.o2o.instance": "cascade"},
        help="Model to export, it should based on the format"
        "[model_name, description of the model]"
        "Example: ['sale.order', 'Sale Order']",
    )

    def prepare_models_fields_to_export(self):
        """Retrieve and merge O2O-specific models configuration for export.

        Extends the base module's model configuration by fetching O2O-specific
        models and fields from system parameters. Additionally handles sensitive
        information fields when export_sensitive_information is enabled, merging
        them with the standard field configurations.

        Returns:
            dict: Combined models and fields configuration including both base
                and O2O-specific configurations, with sensitive fields when enabled

        Raises:
            UserError: When O2O models configuration or sensitive fields
                configuration cannot be parsed, providing guidance on format

        Example:
            >>> result = self.prepare_models_fields_to_export()
            >>> print(result)
            {'foreg.o2o.instance': ['name', 'url'], 'sale.order': ['name']}
        """
        result = super().prepare_models_fields_to_export()
        ICP = self.env["ir.config_parameter"].sudo()
        models_fields = ICP.get_param("4egrowth_data_import_export_o2o_models", "{}")
        try:
            models_fields = json.loads(models_fields)
        except json.JSONDecodeError as e:
            raise UserError(
                _(
                    "Error parsing O2O models configuration: %(error)s. "
                    "Please check the format of the configuration parameter.",
                    error=str(e),
                )
            ) from e
        if self.export_sensitive_information:
            sensitive_fields = ICP.get_param("o2o_export_sensitive_information", "{}")
            try:
                sensitive_fields = json.loads(sensitive_fields)
            except json.JSONDecodeError as e:
                raise UserError(
                    _(
                        "Error parsing O2O sensitive fields configuration: %(error)s. "
                        "Please check the format of the configuration parameter.",
                        error=str(e),
                    )
                ) from e
            for model_name, fields_list in sensitive_fields.items():
                models_fields[model_name] += fields_list
        result.update(models_fields)

        return result

    def get_record_model(self):
        """Get the records to be exported with O2O-specific logic.

        Extends the base method to handle O2O Instance exports specifically.
        When the model is "foreg.o2o.instance", returns the selected O2O instance
        along with related workflow jobs if available. For other models,
        delegates to the parent method.

        Returns:
            list: List of records to be exported. For O2O instances, includes
                the instance record and related workflow jobs. For other models,
                returns the result from the parent method.

        Raises:
            UserError: When model is "foreg.o2o.instance" but no O2O instance
                is selected

        Example:
            >>> records = self.get_record_model()
            >>> print(f"Selected {len(records)} records for export")
            Selected 5 records for export
        """
        self.ensure_one()
        if self.model == "foreg.o2o.instance":
            if not self.o2o_instance_id:
                raise UserError(_("Please select an O2O Instance to export."))
            result = [self.o2o_instance_id]
            if "foreg.o2o.workflow.job" in self.env:
                result += [
                    record
                    for record in self.env["foreg.o2o.workflow.job"]
                    .with_context(active_test=False)
                    .search(
                        [
                            ("instance_id", "=", self.o2o_instance_id.id),
                        ]
                    )
                ]
            return result
        return super().get_record_model()

    def action_export_data(self):
        """Perform data export with O2O instance validation.

        Extends the base export functionality by ensuring that an O2O instance
        is selected before proceeding with the export operation. This validation
        is required for O2O-specific export operations to maintain data integrity
        and proper context.

        Returns:
            dict: Odoo action dictionary from the parent method to display
                the export results to the user

        Raises:
            UserError: When no O2O instance is selected for the export operation

        Example:
            >>> action = self.action_export_data()
            >>> print(action['type'])
            'ir.actions.act_window'
        """
        self.ensure_one()

        if not self.o2o_instance_id:
            raise UserError(_("Please select an O2O Instance to export."))

        return super().action_export_data()
