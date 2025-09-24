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
from datetime import datetime

from odoo import _, fields, models
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT

_logger = logging.getLogger(__name__)


class ForegDataImportExport(models.Model):
    _name = "foreg.data.import.export"
    _description = "4EG Data Import/Export"
    _rec_name = "name"

    name = fields.Char(
        required=True,
        help="Name of the import/export configuration",
    )
    model = fields.Selection(
        [],
        help="Model to export, it should based on the format"
        "[model_name, description of the model]"
        "Example: ['sale.order', 'Sale Order']",
    )
    data_file = fields.Binary(
        string="Data JSON File",
        help="JSON file containing the data to import or the exported data",
    )
    data_filename = fields.Char(
        string="Data JSON Filename",
        help="Name of the data file",
    )
    summary = fields.Html(
        readonly=True,
        help="Summary of the import/export process",
        default="",
    )
    export_sensitive_information = fields.Boolean(
        default=False,
        help="Export sensitive information",
    )

    def prepare_models_fields_to_export(self):
        """Retrieve and parse models configuration for export.

        Fetches the models and fields configuration from system parameters
        and parses the JSON configuration. This configuration determines
        which models and their fields should be included in the export process.

        Returns:
            dict: Parsed models and fields configuration from system parameters.
                Empty dict if parameter is not set or invalid.

        Raises:
            UserError: When JSON configuration parameter cannot be parsed,
                providing guidance on how to fix the format.

        Example:
            >>> result = self.prepare_models_fields_to_export()
            >>> print(result)
            {'sale.order': ['name', 'date_order'], 'res.partner': ['name']}
        """
        self.ensure_one()
        ICP = self.env["ir.config_parameter"].sudo()
        models_fields = ICP.get_param("4egrowth_data_import_export_default_model", "{}")
        try:
            models_fields = json.loads(models_fields)
        except json.JSONDecodeError as e:
            raise UserError(
                _(
                    "Error parsing models configuration: %(error)s. "
                    "Please check the format of the configuration parameter.",
                    error=str(e),
                )
            ) from e
        return models_fields

    def _validate_export_parameters(self):
        """Validate export parameters before starting the export process.

        Performs comprehensive validation of export configuration including
        models configuration availability, record selection, and model
        compatibility. Ensures all necessary conditions are met before
        proceeding with the export operation.

        Returns:
            tuple: Contains (models_fields, list_record) where:
                - models_fields (dict): Parsed models and fields configuration
                - list_record (recordset): Records to be exported

        Raises:
            UserError: When models configuration is missing, when selected
                records belong to unconfigured models, or when no records
                are selected for export.

        Example:
            >>> models_fields, records = self._validate_export_parameters()
            >>> print(f"Models: {list(models_fields.keys())}")
            >>> print(f"Records count: {len(records)}")
        """
        self.ensure_one()

        # Get models and fields to export from config parameter
        models_fields = self.prepare_models_fields_to_export()

        # Validate that models_fields is not empty
        if not models_fields:
            raise UserError(
                _(
                    "No models configuration found for export. "
                    "Please configure models to export in system parameters."
                )
            )

        # Get the record to start with
        list_record = self.get_record_model()

        # Validate that the record's model is in models_fields
        if invalid_models := [
            record._name for record in list_record if record._name not in models_fields
        ]:
            invalid_models = list(set(invalid_models))
            raise UserError(
                _(
                    "The model %(model)s is not configured for export. "
                    "Please add it to the export configuration.",
                    model=", ".join(invalid_models),
                )
            )

        if not list_record:
            raise UserError(_("No record selected for export."))

        return models_fields, list_record

    def _init_export_data_structures(self, start_model, record):
        """Initialize data structures needed for the export process.

        Creates and initializes all necessary data structures that will be
        used throughout the export process to track records, results, and
        processing status. This provides a clean starting state for the
        export operation.

        Args:
            start_model (str): The technical name of the starting model
            record (recordset): The record to begin the export process with

        Returns:
            tuple: Contains (result, processed_records, summary_data,
                pending_records) where:
                - result (dict): Will store the final export data
                - processed_records (dict): Tracks already processed records
                - summary_data (dict): Stores summary information per model
                - pending_records (dict): Queue of records waiting to be processed

        Example:
            >>> result, processed, summary, pending = self._init_export_data_structures(
            ...     'sale.order', order_record
            ... )
            >>> print(f"Pending: {pending}")
            {'sale.order': [123]}
        """
        # Initialize the result dictionary
        result = {}

        # Store processed records to avoid duplicates
        processed_records = {}

        # Store the summary information
        summary_data = {}

        # Process the starting record and its related models
        pending_records = {start_model: [record.id]}

        return result, processed_records, summary_data, pending_records

    def prepare_summary_error(self, error_message):
        """Add an error message to the summary field with formatting.

        Appends an error message to the existing summary field with HTML
        formatting (red color) to distinguish errors from regular summary
        information. If no summary exists yet, creates a new summary with
        the error message.

        Args:
            error_message (str): The error message to be added to the summary

        Example:
            >>> self.prepare_summary_error("Model validation failed")
            >>> print(self.summary)
            "<p style='color: red;'>Model validation failed</p>"
        """
        self.ensure_one()
        if self.summary:
            self.summary += f"<p style='color: red;'>{error_message}</p>"
        else:
            self.summary = f"<p style='color: red;'>{error_message}</p>"

    def _process_many2one_field(
        self,
        field_value,
        field_name,
        field_info,
        record_data,
        pending_records,
        processed_records,
        models_fields,
    ):
        """
        Process a many2one field during export.

        Args:
            field_value: The field value
            field_name: The field name
            field_info: The field info object
            record_data: The record data being built
            pending_records: Dictionary of records pending processing
            processed_records: Dictionary of already processed records
            models_fields: Dictionary of models and fields to export

        Returns:
            tuple: (record_data, pending_records, processed_records)
        """
        if not field_value:
            record_data[field_name] = False
            return record_data, pending_records, processed_records

        # Store M2O as XML ID
        related_model = field_info.comodel_name

        # Special handling for ir.model and ir.model.fields references
        if related_model in ("ir.model", "ir.model.fields"):
            if field_value.state == "manual":
                # For manual models/fields, add to pending records to export their data
                if related_model not in pending_records:
                    pending_records[related_model] = []
                if field_value.id not in pending_records[
                    related_model
                ] and field_value.id not in processed_records.get(related_model, set()):
                    pending_records[related_model].append(field_value.id)
            # Store XML ID for both manual and non-manual
            record_data[field_name] = self._get_or_generate_xml_id(field_value)
            return record_data, pending_records, processed_records

        if related_model in models_fields:
            # Add to pending records for processing
            if related_model not in pending_records:
                pending_records[related_model] = []
            if related_model not in processed_records:
                processed_records[related_model] = set()

            if (
                field_value.id not in pending_records[related_model]
                and field_value.id not in processed_records[related_model]
            ):
                pending_records[related_model].append(field_value.id)

        # Store XML ID reference
        record_data[field_name] = self._get_or_generate_xml_id(field_value)
        return record_data, pending_records, processed_records

    def _process_x2many_field(
        self,
        field_value,
        field_name,
        field_info,
        record_data,
        pending_records,
        processed_records,
        models_fields,
    ):
        """
        Process a one2many or many2many field during export.

        Args:
            field_value: The field value
            field_name: The field name
            field_info: The field info object
            record_data: The record data being built
            pending_records: Dictionary of records pending processing
            processed_records: Dictionary of already processed records
            models_fields: Dictionary of models and fields to export

        Returns:
            tuple: (record_data, pending_records, processed_records)
        """
        related_model = field_info.comodel_name
        if not (related_model in models_fields and field_value):
            record_data[field_name] = []
            return record_data, pending_records, processed_records

        # Add to pending records for processing
        if related_model not in pending_records:
            pending_records[related_model] = []

        if related_model not in processed_records:
            processed_records[related_model] = set()

        # Add all related records to pending
        xml_ids = []

        # Special handling for ir.model and ir.model.fields
        if related_model in ("ir.model", "ir.model.fields"):
            for rel_rec in field_value:
                if rel_rec.state == "manual":
                    # For manual models/fields, add to pending records
                    if (
                        rel_rec.id not in pending_records[related_model]
                        and rel_rec.id not in processed_records[related_model]
                    ):
                        pending_records[related_model].append(rel_rec.id)
                # Store XML ID for both manual and non-manual
                xml_ids.append(self._get_or_generate_xml_id(rel_rec))
        else:
            # For other models, process as before
            for rel_rec in field_value:
                if (
                    rel_rec.id not in pending_records[related_model]
                    and rel_rec.id not in processed_records[related_model]
                ):
                    pending_records[related_model].append(rel_rec.id)
                xml_ids.append(self._get_or_generate_xml_id(rel_rec))

        # Store list of XML IDs
        if field_info.type == "many2many":
            record_data[field_name] = xml_ids

        return record_data, pending_records, processed_records

    def _process_basic_field(self, field_value, field_name, field_info, record_data):
        """Process basic (non-relational) fields during export.

        Handles the conversion and formatting of basic field types including
        datetime, date, and binary fields. For binary fields, applies
        sensitivity filtering based on attachment status and export settings.
        Properly formats datetime and date fields to Odoo's standard formats.

        Args:
            field_value: The current value of the field to process
            field_name (str): The technical name of the field
            field_info: The field definition object containing metadata
            record_data (dict): The record data dictionary being built

        Returns:
            dict: Updated record_data with the processed field value

        Example:
            >>> record_data = {}
            >>> self._process_basic_field(
            ...     datetime.now(), 'create_date', date_field_info, record_data
            ... )
            >>> print(record_data['create_date'])
            '2024-01-15 10:30:00'
        """
        if field_info.type == "datetime" and field_value:
            record_data[field_name] = field_value.strftime(
                DEFAULT_SERVER_DATETIME_FORMAT
            )

        elif field_info.type == "date" and field_value:
            record_data[field_name] = field_value.strftime(DEFAULT_SERVER_DATE_FORMAT)

        elif field_info.type == "binary" and field_value:
            # Only export non-sensitive binary data unless explicitly allowed
            if self.export_sensitive_information or not field_info.attachment:
                try:
                    record_data[field_name] = base64.b64encode(field_value).decode(
                        "utf-8"
                    )
                except Exception:
                    # Handle case where field_value is already base64 encoded
                    record_data[field_name] = (
                        field_value if isinstance(field_value, str) else False
                    )
            else:
                record_data[field_name] = False

        elif field_info.type in ("monetary", "float") and field_value is not None:
            # Ensure proper serialization of float values
            record_data[field_name] = float(field_value)

        elif field_info.type == "integer" and field_value is not None:
            record_data[field_name] = int(field_value)

        elif field_info.type == "boolean":
            record_data[field_name] = bool(field_value)

        elif field_info.type == "selection":
            record_data[field_name] = field_value

        else:
            # Handle other field types (char, text, etc.)
            record_data[field_name] = field_value

        return record_data

    def _add_custom_field_to_pending(
        self, field_name, current_model, pending_records, processed_records
    ):
        """Check if field is custom and add its definition to pending records.

        Searches for a custom (manual) field definition and adds it to the
        pending records queue for export. This ensures custom field definitions
        are included in the export data so they can be recreated during import.
        Only fields with state='manual' are considered custom fields.

        Args:
            field_name (str): The technical name of the field to check
            current_model (str): The model name containing the field
            pending_records (dict): Dictionary tracking records pending processing
            processed_records (dict): Dictionary of already processed records

        Returns:
            bool: True if a custom field was found and added to pending,
                False if the field is not custom or not found

        Example:
            >>> result = self._add_custom_field_to_pending(
            ...     'x_custom_field', 'sale.order', pending_records, processed_records
            ... )
            >>> print(result)
            True
        """
        field_model = self.env["ir.model.fields"].search_fetch(
            [("model", "=", current_model), ("name", "=", field_name)],
            ["id", "state"],
            limit=1,
        )

        if field_model and field_model.state == "manual":
            # This is a custom field, add it to pending_records for ir.model.fields
            if "ir.model.fields" not in pending_records:
                pending_records["ir.model.fields"] = []

            if field_model.id not in pending_records[
                "ir.model.fields"
            ] and field_model.id not in processed_records.get("ir.model.fields", set()):
                pending_records["ir.model.fields"].append(field_model.id)

            return True

        return False

    def _add_related_custom_model_to_pending(
        self, comodel_name, pending_records, processed_records
    ):
        """Check if related model is custom and add it with fields to pending.

        Searches for a custom (manual) model definition and adds both the model
        and all its custom fields to the pending records queue. This ensures
        that custom models and their field definitions are included in the
        export data for proper recreation during import.

        Args:
            comodel_name (str): The technical name of the related model to check
            pending_records (dict): Dictionary tracking records pending processing
            processed_records (dict): Dictionary of already processed records

        Returns:
            bool: True if a custom model was found and added to pending along
                with its custom fields, False if the model is not custom

        Example:
            >>> result = self._add_related_custom_model_to_pending(
            ...     'x_custom_model', pending_records, processed_records
            ... )
            >>> print(result)
            True
        """
        # Check if related model is a custom model
        related_model_info = self.env["ir.model"].search_fetch(
            [("model", "=", comodel_name)], ["id", "state"], limit=1
        )

        if related_model_info and related_model_info.state == "manual":
            # Add custom related model to pending records
            if "ir.model" not in pending_records:
                pending_records["ir.model"] = []

            if related_model_info.id not in pending_records[
                "ir.model"
            ] and related_model_info.id not in processed_records.get("ir.model", set()):
                pending_records["ir.model"].append(related_model_info.id)

            # Also add its custom fields to pending records
            custom_fields = self.env["ir.model.fields"].search_fetch(
                [("model", "=", comodel_name), ("state", "=", "manual")], ["id"]
            )

            if custom_fields:
                if "ir.model.fields" not in pending_records:
                    pending_records["ir.model.fields"] = []

                for cf in custom_fields:
                    if cf.id not in pending_records[
                        "ir.model.fields"
                    ] and cf.id not in processed_records.get("ir.model.fields", set()):
                        pending_records["ir.model.fields"].append(cf.id)

            return True

        return False

    def _process_field(
        self,
        rec,
        field_name,
        field_info,
        record_data,
        pending_records,
        processed_records,
        models_fields,
        current_model,
    ):
        """Process a single field value during the export operation.

        Handles the complete processing of a field including custom field
        detection, related model checking, and appropriate field value
        conversion based on field type. Routes processing to specialized
        methods for different field types (many2one, x2many, basic fields).

        Args:
            rec (recordset): The record being processed
            field_name (str): The technical name of the field to process
            field_info: The field definition object containing metadata
            record_data (dict): The record data dictionary being built
            pending_records (dict): Dictionary tracking records pending processing
            processed_records (dict): Dictionary of already processed records
            models_fields (dict): Configuration of models and fields to export
            current_model (str): The technical name of the current model

        Returns:
            tuple: Contains (record_data, pending_records, processed_records)
                with updated values after field processing

        Raises:
            UserError: When field processing encounters an unrecoverable error

        Example:
            >>> record_data, pending, processed = self._process_field(
            ...     sale_order, 'partner_id', field_info, {}, {}, {},
            ...     models_config, 'sale.order'
            ... )
            >>> print(record_data['partner_id'])
            '__export__.res_partner_123'
        """
        try:
            # Check if this is a custom field (state = 'manual')
            # If yes, make sure we export this field's definition
            self._add_custom_field_to_pending(
                field_name, current_model, pending_records, processed_records
            )

            # Check if field is a relation field (many2one, one2many, many2many)
            # If yes, check if the related model is a custom model
            if field_info.type in ("many2one", "one2many", "many2many") and hasattr(
                field_info, "comodel_name"
            ):
                self._add_related_custom_model_to_pending(
                    field_info.comodel_name, pending_records, processed_records
                )

            field_value = rec[field_name]

            # Handle different field types
            if field_info.type == "many2one":
                (
                    record_data,
                    pending_records,
                    processed_records,
                ) = self._process_many2one_field(
                    field_value,
                    field_name,
                    field_info,
                    record_data,
                    pending_records,
                    processed_records,
                    models_fields,
                )

            elif field_info.type in ("one2many", "many2many"):
                (
                    record_data,
                    pending_records,
                    processed_records,
                ) = self._process_x2many_field(
                    field_value,
                    field_name,
                    field_info,
                    record_data,
                    pending_records,
                    processed_records,
                    models_fields,
                )

            else:
                record_data = self._process_basic_field(
                    field_value, field_name, field_info, record_data
                )

        except Exception as e:
            error_message = f"Error processing field {field_name} for "
            f"record {rec.id} of model {current_model}: {str(e)}"
            _logger.error(error_message)
            self.prepare_summary_error(error_message)
            record_data[field_name] = False

        return record_data, pending_records, processed_records

    def _filter_records_for_export(
        self, current_model, current_record_ids, processed_records
    ):
        """Filter and prepare records for export with special model handling.

        Filters out already processed records and applies special filtering
        rules for system models. For ir.model and ir.model.fields, only
        includes records with state='manual' (custom models/fields).
        Uses active_test=False to include archived records in the export.

        Args:
            current_model (str): The technical name of the model being processed
            current_record_ids (list): List of record IDs to process
            processed_records (dict): Dictionary tracking already processed records

        Returns:
            recordset or None: Filtered records ready for processing, or None
                if no records remain after filtering

        Example:
            >>> records = self._filter_records_for_export(
            ...     'sale.order', [1, 2, 3], {'sale.order': {1}}
            ... )
            >>> print(len(records))
            2
        """
        # Filter out already processed records
        record_ids_to_process = [
            rid
            for rid in current_record_ids
            if rid not in processed_records.get(current_model, set())
        ]

        if not record_ids_to_process:
            return None

        # Fetch records with active_test=False to include archived records
        current_records = (
            self.env[current_model]
            .with_context(active_test=False)
            .browse(record_ids_to_process)
        )

        # Special handling for ir.model and ir.model.fields: only export manual types
        if current_model == "ir.model":
            current_records = current_records.filtered(lambda r: r.state == "manual")
        elif current_model == "ir.model.fields":
            current_records = current_records.filtered(lambda r: r.state == "manual")

        return current_records

    def _process_model_records(
        self,
        current_model,
        current_records,
        valid_fields,
        result,
        summary_data,
        pending_records,
        processed_records,
        models_fields,
    ):
        """Process all records for a specific model during export.

        Iterates through all records of a given model and processes each
        field according to the export configuration. Generates XML IDs,
        processes field values, and builds the export data structure.
        Updates tracking dictionaries to maintain export state.

        Args:
            current_model (str): The technical name of the model being processed
            current_records (recordset): Records to process for this model
            valid_fields (list): List of field names to include in export
            result (dict): The main export result dictionary being built
            summary_data (dict): Dictionary tracking export statistics
            pending_records (dict): Dictionary of records waiting to be processed
            processed_records (dict): Dictionary of already processed records
            models_fields (dict): Configuration of models and fields to export

        Returns:
            tuple: Contains (result, summary_data, pending_records,
                processed_records) with all dictionaries updated after
                processing the current model's records

        Example:
            >>> result, summary, pending, processed = self._process_model_records(
            ...     'sale.order', order_records, ['name', 'date_order'],
            ...     {}, {}, {}, {}, models_config
            ... )
            >>> print(f"Processed {summary['sale.order']} orders")
        """
        model_fields = self.env[current_model]._fields

        for rec in current_records:
            # Mark as processed
            processed_records[current_model].add(rec.id)

            # Get or generate XML ID for the record
            xml_id = self._get_or_generate_xml_id(rec)

            # Initialize record data
            record_data = {"id": rec.id}

            # Process each field
            for field_name in valid_fields:
                record_data, pending_records, processed_records = self._process_field(
                    rec,
                    field_name,
                    model_fields[field_name],
                    record_data,
                    pending_records,
                    processed_records,
                    models_fields,
                    current_model,
                )

            # Add record data to result
            result[current_model][xml_id] = record_data
            summary_data[current_model] = summary_data.get(current_model, 0) + 1

        return result, summary_data, pending_records, processed_records

    def _save_export_results(self, result, summary_data):
        """Save export results and generate summary for the user.

        Converts the export result to a formatted JSON file, encodes it as
        base64, and stores it in the data_file field. Also generates a
        comprehensive HTML summary showing the export statistics and stores
        it for user review.

        Args:
            result (dict): The complete export result containing all models
                and their records
            summary_data (dict): Dictionary containing export statistics
                per model (count of exported records)

        Returns:
            dict: Odoo action dictionary to display the updated form view
                to the user

        Example:
            >>> action = self._save_export_results(
            ...     {'sale.order': {'order_1': {...}}},
            ...     {'sale.order': 1}
            ... )
            >>> print(action['type'])
            'ir.actions.act_window'
        """
        # Convert to JSON and encode as base64
        result_json = json.dumps(result, indent=4, sort_keys=True, default=str)
        export_filename = f"{self.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        # Update record with export data
        self.write(
            {
                "data_file": base64.b64encode(result_json.encode("utf-8")),
                "data_filename": export_filename,
                "summary": self._generate_export_summary(summary_data),
            }
        )

        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "target": "current",
        }

    def get_record_model(self):
        """Get the records to be exported based on context or configuration.

        This method should be overridden in inherited modules to provide
        the actual records to export. The base implementation returns False
        to indicate no records are selected, which will trigger an error
        in the validation phase.

        Returns:
            recordset or False: The records to be exported, or False if
                no records are selected

        Example:
            >>> records = self.get_record_model()
            >>> print(f"Selected {len(records)} records for export")
        """
        self.ensure_one()
        return False

    def action_export_data(self):
        """
        Export the data to a JSON file

        Exports records based on the specified model and its related data.
        For relational fields (m2o, o2m, m2m), it extracts XML IDs.
        The function also includes XML IDs for each record
        or generates them if not found.

        The output format is:
        {
            "<model_name>": {
                "<xml_id>": {
                    "id": <id>,
                    "<field_name>": <value>,
                    ...
                } ...
            } ...
        }

        Export Rules:
        - Includes archived records (context active_test=False)
        - Converts field values appropriately based on field type
        - Handles relational fields differently based on the related model
        - Special handling for system models (ir.model, ir.model.fields, etc.)
        - Sorts the JSON result alphabetically
        """
        self.ensure_one()

        _logger.info(
            "[Export] Starting export for record ID %s, model %s", self.id, self.model
        )
        # Get model from context or field
        if not self.model:
            raise UserError(_("Please select a model to export."))

        # Validate export parameters
        models_fields, list_record = self._validate_export_parameters()

        # Initialize data structures
        result = {}

        # Store processed records to avoid duplicates
        processed_records = {}

        # Store the summary information
        summary_data = {}

        # Process the starting record and its related models
        pending_records = {}
        for record in list_record:
            pending_records.setdefault(record._name, []).append(record.id)

        # Process all records and their relations iteratively
        while pending_records:
            current_model = list(pending_records.keys())[0]
            current_record_ids = pending_records.pop(current_model)

            _logger.info(
                "[Export] Processing model: %s, record IDs: %s",
                current_model,
                current_record_ids,
            )
            # Skip if model not in models_fields
            if current_model not in models_fields:
                _logger.info(
                    "[Export] Skipping model %s as it is not in models_fields",
                    current_model,
                )
                continue

            # Initialize model in result and summary if needed
            if current_model not in result:
                result[current_model] = {}

            if current_model not in summary_data:
                summary_data[current_model] = 0

            if current_model not in processed_records:
                processed_records[current_model] = set()

            # Get fields to export for this model
            fields_to_export = models_fields.get(current_model, [])
            if not fields_to_export:
                _logger.info("[Export] No fields to export for model %s", current_model)
                continue

            # Filter and fetch records to process
            current_records = self._filter_records_for_export(
                current_model, current_record_ids, processed_records
            )

            # Skip if no records to process after filtering
            if not current_records:
                _logger.info(
                    "[Export] No records to process for model %s after filtering",
                    current_model,
                )
                continue

            # Validate field list
            model_fields = self.env[current_model]._fields
            valid_fields = [f for f in fields_to_export if f in model_fields]

            # Process all records for this model
            (
                result,
                summary_data,
                pending_records,
                processed_records,
            ) = self._process_model_records(
                current_model,
                current_records,
                valid_fields,
                result,
                summary_data,
                pending_records,
                processed_records,
                models_fields,
            )
            _logger.info("[Export] Finished processing model: %s", current_model)

        _logger.info("[Export] Export completed for record ID %s", self.id)
        # Save results and return action
        return self._save_export_results(result, summary_data)

    def _generate_export_summary(self, summary_data):
        """Generate an HTML summary of the export operation results.

        Creates a formatted HTML summary showing the number of records
        exported per model and the total count. The summary is sorted
        alphabetically by model name for consistent presentation.

        Args:
            summary_data (dict): Dictionary mapping model names to the count
                of records exported for each model

        Returns:
            str: HTML-formatted summary string ready for display in the UI

        Example:
            >>> summary = self._generate_export_summary({
            ...     'sale.order': 5, 'res.partner': 3
            ... })
            >>> print(summary)
            '<p>Export completed successfully:</p><ul>...'
        """
        # Build summary HTML
        lines = []
        total_records = 0

        for model, count in sorted(summary_data.items()):
            lines.append(f"<li>{model}: {count} records</li>")
            total_records += count

        summary = f"""
            <p>Export completed successfully:</p>
            <ul>
                {"".join(lines)}
            </ul>
            <p>Total records exported: {total_records}</p>
        """

        return summary

    def _get_or_generate_xml_id(self, record):
        """Get existing XML ID for a record or generate a new one.

        Searches for an existing XML ID (external identifier) for the given
        record. If no XML ID exists, generates a new one using the pattern
        '__export__.{model}_{id}'. This ensures every record can be properly
        referenced during import operations.

        Args:
            record (recordset): Single record to get or generate XML ID for

        Returns:
            str: The XML ID for the record, either existing or newly generated

        Example:
            >>> xml_id = self._get_or_generate_xml_id(partner_record)
            >>> print(xml_id)
            '__export__.res_partner_123'
        """
        self.ensure_one()

        # Try to find existing XML ID
        xml_id = self.env["ir.model.data"].search_fetch(
            [
                ("model", "=", record._name),
                ("res_id", "=", record.id),
            ],
            ["name", "module"],
            limit=1,
        )
        if xml_id:
            return xml_id.complete_name
        # Generate a new XML ID if not found
        xmlid = record._BaseModel__ensure_xml_id()
        xmlid = list(xmlid)[0][1]

        return xmlid

    def _handle_one2one_field(
        self,
        value,
        field_name,
        field_info,
        data,
        created_records,
        processing_stack=None,
        skipped_relations=None,
        current_model=None,
        current_xml_id=None,
    ):
        """Handle one2one field processing during import operations.

        Processes one2one relational fields by resolving XML ID references
        to actual record IDs. Handles circular references by deferring
        problematic relations to a second pass. Creates related records
        if they don't exist and are available in the import data.

        Args:
            value (str): The XML ID of the related record
            field_name (str): The name of the field being processed
            field_info: The field definition object containing metadata
            data (dict): The complete import data containing all models
            created_records (dict): Tracking dictionary of created records
            processing_stack (set, optional): Stack to detect circular references
            skipped_relations (list, optional): List of deferred relations
            current_model (str, optional): The current model being processed
            current_xml_id (str, optional): The current record's XML ID

        Returns:
            int or False: The ID of the related record if found/created,
                False if the relation was skipped due to circular reference

        Example:
            >>> record_id = self._handle_one2one_field(
            ...     '__export__.res_partner_123', 'partner_id', field_info,
            ...     import_data, created_records
            ... )
            >>> print(record_id)
            123
        """
        related_model = field_info.comodel_name
        if processing_stack is None:
            processing_stack = set()
        if skipped_relations is None:
            skipped_relations = []

        # Prevent infinite recursion
        if (related_model, value) in processing_stack:
            _logger.warning(
                f"Detected circular reference for model {related_model}, "
                f"value {value} in field {field_name}. "
                "Skipping to prevent infinite recursion."
            )
            # Record for second pass
            skipped_relations.append(
                {
                    "model": current_model,
                    "xml_id": current_xml_id,
                    "field_name": field_name,
                    "related_model": related_model,
                    "related_xml_id": value,
                }
            )
            return False

        # Check if record was already created in this import process
        if related_model in created_records and value in created_records[related_model]:
            return created_records[related_model][value].id

        # Look up record by XML ID
        related_record = self.env.ref(value, raise_if_not_found=False)
        if related_record:
            return related_record.id

        if related_model in data and value in data.get(related_model, {}):
            # Create the related record
            rel_data = data[related_model][value]
            rel_values, created_records = self.prepare_values(
                rel_data,
                data,
                related_model,
                created_records,
                processing_stack | {(related_model, value)},
                skipped_relations,
                related_model,
                value,
            )
            new_record = self.env[related_model].create(rel_values)

            # Create ir.model.data entry if it doesn't exist
            module, name = (
                value.split(".", 1) if "." in value else ("__export__", value)
            )
            # If user delete a record, xml id was not deleted
            # So we need to find the existing ir.model.data entry
            existing_ir_model_data = (
                self.env["ir.model.data"]
                .sudo()
                .search(
                    [
                        ("module", "=", module),
                        ("name", "=", name),
                    ]
                )
            )
            if existing_ir_model_data:
                existing_ir_model_data.sudo().write(
                    {
                        "res_id": new_record.id,
                        "model": related_model,
                    }
                )
            else:
                self.env["ir.model.data"].sudo().create(
                    {
                        "model": related_model,
                        "res_id": new_record.id,
                        "module": module,
                        "name": name,
                    }
                )

            # Track the created record
            if related_model not in created_records:
                created_records[related_model] = {}
            created_records[related_model][value] = new_record

            return new_record.id

        error_message = (
            f"Related record {value} for field {field_name} "
            f"in model {related_model} not found"
        )
        _logger.warning(error_message)
        self.prepare_summary_error(error_message)
        return False

    def _handle_many2one_field(
        self,
        value,
        field_name,
        field_info,
        data,
        created_records,
        processing_stack,
        skipped_relations,
        current_model,
        current_xml_id,
    ):
        """Handle many2one field processing during import operations.

        Processes many2one relational fields by resolving XML ID references
        to actual record IDs. Handles circular dependencies by deferring
        problematic relations. Creates related records recursively if they
        don't exist but are available in the import data.

        Args:
            value (str): The XML ID of the related record
            field_name (str): The name of the field being processed
            field_info: The field definition object containing metadata
            data (dict): The complete import data containing all models
            created_records (dict): Tracking dictionary of created records
            processing_stack (set): Stack to detect circular references
            skipped_relations (list): List of deferred relations
            current_model (str): The current model being processed
            current_xml_id (str): The current record's XML ID

        Returns:
            int or False: The ID of the related record if found/created,
                False if the relation was skipped due to circular reference

        Example:
            >>> record_id = self._handle_many2one_field(
            ...     '__export__.res_partner_123', 'partner_id', field_info,
            ...     import_data, created_records, set(), [], 'sale.order', 'order_1'
            ... )
            >>> print(record_id)
            123
        """
        related_model = field_info.comodel_name

        # Prevent infinite recursion
        if (related_model, value) in processing_stack:
            _logger.warning(
                f"Detected circular reference for model {related_model}, "
                "value {value} in field {field_name}. "
                "Skipping to prevent infinite recursion."
            )
            # Record for second pass
            skipped_relations.append(
                {
                    "model": current_model,
                    "xml_id": current_xml_id,
                    "field_name": field_name,
                    "related_model": related_model,
                    "related_xml_id": value,
                }
            )
            return False

        # Check if record was already created in this import process
        if related_model in created_records and value in created_records[related_model]:
            return created_records[related_model][value].id

        # Look up record by XML ID
        related_record = self.env.ref(value, raise_if_not_found=False)
        if related_record:
            return related_record.id
        if related_model in data and value in data.get(related_model, {}):
            # Create the related record
            rel_data = data[related_model][value]
            rel_values, created_records = self.prepare_values(
                rel_data,
                data,
                related_model,
                created_records,
                processing_stack | {(related_model, value)},
                skipped_relations,
                related_model,
                value,
            )
            new_record = self.env[related_model].create(rel_values)

            # Create ir.model.data entry if it doesn't exist
            module, name = (
                value.split(".", 1) if "." in value else ("__export__", value)
            )
            # If user delete a record, xml id was not deleted
            # So we need to find the existing ir.model.data entry
            existing_ir_model_data = (
                self.env["ir.model.data"]
                .sudo()
                .search(
                    [
                        ("module", "=", module),
                        ("name", "=", name),
                    ]
                )
            )
            if existing_ir_model_data:
                existing_ir_model_data.sudo().write(
                    {
                        "res_id": new_record.id,
                        "model": related_model,
                    }
                )
            else:
                self.env["ir.model.data"].sudo().create(
                    {
                        "model": related_model,
                        "res_id": new_record.id,
                        "module": module,
                        "name": name,
                    }
                )

            # Track the created record
            if related_model not in created_records:
                created_records[related_model] = {}
            created_records[related_model][value] = new_record

            return new_record.id

        error_message = (
            f"Related record {value} for field {field_name} "
            f"in model {related_model} not found"
        )
        _logger.warning(error_message)
        self.prepare_summary_error(error_message)
        return False

    def _handle_many2many_field(
        self, value, field_name, field_info, data, created_records
    ):
        """Handle many2many field processing during import operations.

        Processes many2many relational fields by resolving a list of XML ID
        references to actual record IDs. Creates related records if they
        don't exist but are available in the import data. Returns a list
        of record IDs for the many2many relationship.

        Args:
            value (list): List of XML IDs of the related records
            field_name (str): The name of the field being processed
            field_info: The field definition object containing metadata
            data (dict): The complete import data containing all models
            created_records (dict): Tracking dictionary of created records

        Returns:
            list: List of record IDs for the many2many relationship

        Example:
            >>> record_ids = self._handle_many2many_field(
            ...     ['__export__.product_1', '__export__.product_2'],
            ...     'product_ids', field_info, import_data, created_records
            ... )
            >>> print(record_ids)
            [1, 2]
        """
        related_model = field_info.comodel_name
        related_ids = []

        for xml_id in value:
            # Check if record was already created in this import process
            if (
                related_model in created_records
                and xml_id in created_records[related_model]
            ):
                related_ids.append(created_records[related_model][xml_id].id)
                continue

            related_record = self.env.ref(xml_id, raise_if_not_found=False)
            if related_record:
                related_ids.append(related_record.id)
            elif related_model in data and xml_id in data.get(related_model, {}):
                # Create the related record
                rel_data = data[related_model][xml_id]
                rel_values, created_records = self.prepare_values(
                    rel_data, data, related_model, created_records
                )
                new_record = self.env[related_model].create(rel_values)

                # Create ir.model.data entry
                module, name = (
                    xml_id.split(".", 1) if "." in xml_id else ("__export__", xml_id)
                )
                # If user delete a record, xml id was not deleted
                # So we need to find the existing ir.model.data entry
                existing_ir_model_data = (
                    self.env["ir.model.data"]
                    .sudo()
                    .search(
                        [
                            ("module", "=", module),
                            ("name", "=", name),
                        ]
                    )
                )
                if existing_ir_model_data:
                    existing_ir_model_data.sudo().write(
                        {
                            "res_id": new_record.id,
                            "model": related_model,
                        }
                    )
                else:
                    self.env["ir.model.data"].sudo().create(
                        {
                            "model": related_model,
                            "res_id": new_record.id,
                            "module": module,
                            "name": name,
                        }
                    )

                # Track the created record
                if related_model not in created_records:
                    created_records[related_model] = {}
                created_records[related_model][xml_id] = new_record

                related_ids.append(new_record.id)
            else:
                error_message = (
                    f"Related record {xml_id} for field {field_name} "
                    f"in model {related_model} not found"
                )
                _logger.warning(error_message)
                self.prepare_summary_error(error_message)

        return [(6, 0, related_ids)] if related_ids else []

    def prepare_values(
        self,
        values,
        data,
        model,
        created_records=None,
        processing_stack=None,
        skipped_relations=None,
        current_model=None,
        current_xml_id=None,
    ):
        """Prepare and convert field values for record creation during import.

        Processes all field values in a record, handling relational fields
        by resolving XML ID references and converting them to appropriate
        values for Odoo's ORM. Manages circular dependencies and tracks
        record creation to prevent duplicates.

        Args:
            values (dict): The raw field values from the import data
            data (dict): The complete import data containing all models
            model (str): The technical name of the target model
            created_records (dict, optional): Dictionary tracking created records
            processing_stack (set, optional): Set tracking currently processing
                (model, xml_id) pairs to detect circular references
            skipped_relations (list, optional): List tracking skipped relations
                for second-pass processing
            current_model (str, optional): The current model being processed
            current_xml_id (str, optional): The current record's XML ID

        Returns:
            tuple: Contains (prepared_values, created_records) where:
                - prepared_values (dict): Values ready for record creation
                - created_records (dict): Updated tracking of created records

        Raises:
            ValidationError: When field processing encounters validation errors

        Example:
            >>> prepared, created = self.prepare_values(
            ...     {'name': 'Test', 'partner_id': '__export__.res_partner_1'},
            ...     import_data, 'sale.order', {}
            ... )
            >>> print(prepared['partner_id'])
            123
        """
        if created_records is None:
            created_records = {}
        if processing_stack is None:
            processing_stack = set()
        if skipped_relations is None:
            skipped_relations = []
        if current_model is None:
            current_model = model
        if current_xml_id is None:
            current_xml_id = values.get("xml_id", None)

        _logger.info(
            "[Import] Preparing values for model: %s, values keys: %s",
            model,
            list(values.keys()),
        )
        model_fields = self.env[model]._fields
        result = {}

        for field_name, value in values.items():
            # Skip id field
            if field_name == "id":
                continue

            # Handle relational fields
            if field_name in model_fields:
                field_type = model_fields[field_name].type
                _logger.debug(
                    "[Import] Processing field '%s' (type: %s) for model %s",
                    field_name,
                    field_type,
                    model,
                )

                if field_type in ["datetime", "date"] and value:
                    result[field_name] = value
                elif field_type == "one2one" and value:
                    _logger.info(
                        "[Import] Handling one2one field '%s' for model %s",
                        field_name,
                        model,
                    )
                    result[field_name] = self._handle_one2one_field(
                        value,
                        field_name,
                        model_fields[field_name],
                        data,
                        created_records,
                        processing_stack | {(model, value)},
                        skipped_relations,
                        current_model,
                        current_xml_id,
                    )
                elif field_type == "many2one" and value:
                    _logger.info(
                        "[Import] Handling many2one field '%s' for model %s",
                        field_name,
                        model,
                    )
                    result[field_name] = self._handle_many2one_field(
                        value,
                        field_name,
                        model_fields[field_name],
                        data,
                        created_records,
                        processing_stack | {(model, value)},
                        skipped_relations,
                        current_model,
                        current_xml_id,
                    )
                elif field_type == "many2many" and value:
                    _logger.info(
                        "[Import] Handling many2many field '%s' for model %s",
                        field_name,
                        model,
                    )
                    result[field_name] = self._handle_many2many_field(
                        value,
                        field_name,
                        model_fields[field_name],
                        data,
                        created_records,
                    )
                elif field_type == "one2many" and value:
                    # For one2many, we store the XML IDs and will
                    # create them after the parent record
                    # They will be processed later since they need the parent record ID
                    _logger.info(
                        "[Import] Handling one2many field '%s' for model %s (deferred)",
                        field_name,
                        model,
                    )
                    result[field_name] = ""
                else:
                    result[field_name] = value
            else:
                _logger.debug(
                    "[Import] Field '%s' not found in model %s fields, storing as is",
                    field_name,
                    model,
                )
                result[field_name] = value

        _logger.info("[Import] Prepared values for model %s: %s", model, result)
        return result, created_records

    def _set_skipped_relations(self, skipped_relations, created_records):
        """Process and set deferred relational fields after record creation.

        Handles relational fields that were skipped during the initial import
        pass due to circular dependencies. Now that all records have been
        created, attempts to resolve and set these deferred relationships.

        Args:
            skipped_relations (list): List of dictionaries containing deferred
                relation information with keys: model, xml_id, field_name,
                related_model, related_xml_id
            created_records (dict): Dictionary tracking all created records
                during the import process

        Example:
            >>> skipped = [{'model': 'sale.order', 'xml_id': 'order_1',
            ...             'field_name': 'partner_id', 'related_model': 'res.partner',
            ...             'related_xml_id': 'partner_1'}]
            >>> self._set_skipped_relations(skipped, created_records)
        """
        for rel in skipped_relations:
            model = rel["model"]
            xml_id = rel["xml_id"]
            field_name = rel["field_name"]
            related_model = rel["related_model"]
            related_xml_id = rel["related_xml_id"]

            # Find the main record and the related record
            main_record = None
            related_record = None
            if model in created_records and xml_id in created_records[model]:
                main_record = created_records[model][xml_id]
            else:
                try:
                    main_record = self.env.ref(xml_id, raise_if_not_found=False)
                except Exception:
                    main_record = None

            if (
                related_model in created_records
                and related_xml_id in created_records[related_model]
            ):
                related_record = created_records[related_model][related_xml_id]
            else:
                try:
                    related_record = self.env.ref(
                        related_xml_id, raise_if_not_found=False
                    )
                except Exception:
                    related_record = None

            if main_record and related_record:
                try:
                    main_record.sudo().write({field_name: related_record.id})
                    _logger.info(
                        f"Set {model}.{field_name} for {xml_id} to "
                        f"{related_model} {related_xml_id}"
                    )
                except Exception as e:
                    _logger.error(
                        f"Failed to set {model}.{field_name} for {xml_id}: {e}"
                    )
            else:
                _logger.warning(
                    f"Could not set {model}.{field_name} for {xml_id}"
                    " (main or related record not found)"
                )

    def action_import_data(self):
        """
        Import the data from a JSON file

        Imports records from the JSON file, handling relational fields:
        - For many2one fields: Creates related records if they don't exist
        - For many2many fields: Creates related records and links them
        - For one2many fields: Creates related records with the parent reference

        Tracks created records to avoid duplicate creation or updates.
        """
        self.ensure_one()

        _logger.info("[Import] Starting import for record ID %s", self.id)
        if not self.data_file:
            raise UserError(_("No file to import. Please upload a JSON file."))

        try:
            data_json = base64.b64decode(self.data_file).decode("utf-8")
            data = json.loads(data_json)
        except Exception as e:
            raise UserError(
                _(
                    "Error decoding JSON file: %(error)s",
                    error=str(e),
                )
            ) from e

        if not isinstance(data, dict):
            raise UserError(
                _("Invalid JSON format. The file should contain a dictionary.")
            )

        # Initialize counters for summary and tracking created records
        created_count = {}
        updated_count = {}
        created_records = {}
        skipped_relations = []

        # Prioritize model processing: ir.model first,
        #  then ir.model.fields, then other models
        models_to_process = self._prioritize_models_for_import(data)
        ir_model_data_env = self.env["ir.model.data"]
        # Process models in the prioritized order
        for model in models_to_process:
            _logger.info("[Import] Processing model: %s", model)
            records_values = data.get(model, {})
            if model not in self.env:
                error_message = f"Model {model} does not exist in the environment"
                _logger.warning(error_message)
                self.prepare_summary_error(error_message)
                continue

            if model not in created_count:
                created_count[model] = 0
                updated_count[model] = 0

            for xml_id, values in records_values.items():
                # Skip if already created in this import process
                if model in created_records and xml_id in created_records[model]:
                    _logger.info(
                        f"[Import] Record {xml_id} of model {model}"
                        " already created, skipping"
                    )
                    continue

                prepared_values, created_records = self.prepare_values(
                    values,
                    data,
                    model,
                    created_records,
                    processing_stack=None,
                    skipped_relations=skipped_relations,
                    current_model=model,
                    current_xml_id=xml_id,
                )

                record = self.env.ref(xml_id, raise_if_not_found=False)

                if model == "ir.model.fields" and not record:
                    record = self.env["ir.model.fields"].search_fetch(
                        [
                            ("name", "=", prepared_values.get("name")),
                            ("model_id", "=", prepared_values.get("model_id")),
                        ],
                        ["id"],
                        limit=1,
                    )

                if record:
                    # Update existing record
                    record.sudo().write(prepared_values)
                    updated_count[model] += 1
                    _logger.info(
                        "[Import] Updated record %s in model %s", xml_id, model
                    )

                    # Add to created records to avoid duplicate processing
                    if model not in created_records:
                        created_records[model] = {}
                    created_records[model][xml_id] = record

                else:
                    new_record = self.env[model].sudo().create(prepared_values)
                    _logger.info(
                        "[Import] Created new record %s in model %s", xml_id, model
                    )

                    if model == "ir.model":
                        self.env["ir.model.access"].sudo().create(
                            {
                                "name": new_record.name,
                                "model_id": new_record.id,
                                "group_id": self.env.ref("base.group_user").id,
                                "perm_read": 1,
                                "perm_write": 1,
                                "perm_unlink": 1,
                                "perm_create": 1,
                            }
                        )
                    created_count[model] += 1

                    # Create ir.model.data entry
                    module, name = (
                        xml_id.split(".", 1)
                        if "." in xml_id
                        else ("__export__", xml_id)
                    )

                    # If user delete a record, xml id was not deleted
                    # So we need to find the existing ir.model.data entry
                    existing_ir_model_data = ir_model_data_env.sudo().search(
                        [
                            ("module", "=", module),
                            ("name", "=", name),
                        ]
                    )
                    if existing_ir_model_data:
                        existing_ir_model_data.sudo().write(
                            {
                                "res_id": new_record.id,
                            }
                        )
                    else:
                        ir_model_data_env.sudo().create(
                            {
                                "model": model,
                                "res_id": new_record.id,
                                "module": module,
                                "name": name,
                            }
                        )

                    # Add to created records to avoid duplicate processing
                    if model not in created_records:
                        created_records[model] = {}
                    created_records[model][xml_id] = new_record
            _logger.info("[Import] Finished processing model: %s", model)

        # After all records are created, set skipped many2one/one2one fields
        self._set_skipped_relations(skipped_relations, created_records)

        # Generate summary
        summary_data = self.get_summary_data(created_count, updated_count)

        # Update record with summary
        summary_html = self._generate_import_summary(summary_data)
        self.write(
            {
                "summary": summary_html,
            }
        )

        _logger.info("[Import] Import completed for record ID %s", self.id)
        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "target": "current",
        }

    def get_summary_data(self, created_count, updated_count):
        """Generate summary data from import operation counters.

        Combines created and updated record counts into a readable format
        for each model. Provides clear indication of what operations were
        performed during the import process.

        Args:
            created_count (dict): Dictionary mapping model names to count
                of newly created records
            updated_count (dict): Dictionary mapping model names to count
                of updated records

        Returns:
            dict: Dictionary mapping model names to formatted status strings
                showing created/updated counts

        Example:
            >>> summary = self.get_summary_data(
            ...     {'sale.order': 2}, {'res.partner': 1}
            ... )
            >>> print(summary)
            {'sale.order': '2 created', 'res.partner': '1 updated'}
        """
        summary_data = {}
        for model in set(list(created_count.keys()) + list(updated_count.keys())):
            created = created_count.get(model, 0)
            updated = updated_count.get(model, 0)

            if created > 0 and updated > 0:
                summary_data[model] = f"{created} created, {updated} updated"
            elif created > 0:
                summary_data[model] = f"{created} created"
            elif updated > 0:
                summary_data[model] = f"{updated} updated"

        return summary_data

    def _generate_import_summary(self, summary_data):
        """Generate an HTML summary of the import operation results.

        Creates a formatted HTML summary showing the results of the import
        operation for each model. The summary includes creation and update
        counts to provide clear feedback to the user about what was processed.

        Args:
            summary_data (dict): Dictionary mapping model names to formatted
                status strings showing created/updated counts

        Returns:
            str: HTML-formatted summary string ready for display in the UI

        Example:
            >>> summary = self._generate_import_summary({
            ...     'sale.order': '2 created', 'res.partner': '1 updated'
            ... })
            >>> print(summary)
            '<p>Import completed successfully:</p><ul>...'
        """
        # Build summary HTML
        lines = []

        for model, status in sorted(summary_data.items()):
            lines.append(f"<li>{model}: {status}</li>")

        summary = f"""
            <p>Import completed successfully:</p>
            <ul>
                {"".join(lines)}
            </ul>
        """

        return summary

    def _prioritize_models_for_import(self, data):
        """Determine the order of model processing during import operations.

        Establishes a specific processing order to handle model dependencies
        correctly. System models (ir.model, ir.model.fields) are processed
        first to ensure custom models and fields are created before their
        dependent records.

        Args:
            data (dict): The complete import data containing all models
                as keys and their records as values

        Returns:
            list: Ordered list of model names for processing, with system
                models first followed by all other models

        Example:
            >>> models = self._prioritize_models_for_import({
            ...     'sale.order': {...}, 'ir.model': {...}, 'res.partner': {...}
            ... })
            >>> print(models)
            ['ir.model', 'ir.model.fields', 'sale.order', 'res.partner']
        """
        models_to_process = []
        if "ir.model" in data:
            models_to_process.append("ir.model")
        if "ir.model.fields" in data:
            models_to_process.append("ir.model.fields")

        # Add other models
        for model in data.keys():
            if model not in models_to_process:
                models_to_process.append(model)

        return models_to_process
