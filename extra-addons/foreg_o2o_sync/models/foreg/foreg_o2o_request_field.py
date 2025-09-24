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

from odoo import api, fields, models


class ForegO2oRequestField(models.Model):
    """4EG O2O Request Field for field mapping configuration.

    This model defines field mappings between SAAS and local Odoo systems
    for O2O synchronization operations. It handles field relationships,
    data transformations, and mapping rules.
    """

    _name = "foreg.o2o.request.field"
    _description = "4EG O2O Request Field"
    _order = "request_id, model_id, source_field_name"

    request_id = fields.Many2one(
        comodel_name="foreg.o2o.request",
        required=True,
        ondelete="cascade",
        help=(
            "Reference to the O2O request this field "
            "mapping belongs to. Defines the overall "
            "synchronization configuration."
        ),
    )
    name = fields.Char(
        compute="_compute_name",
        store=True,
        help="Name of the field mapping.",
    )
    request_method = fields.Selection(
        selection=[
            ("read", "Read"),
            ("create", "Create"),
            ("update", "Update"),
            ("call_method", "Call Method"),
        ],
        required=True,
        help=(
            "Specifies the operation type for "
            "this field mapping: read data, create new "
            "records, update existing ones, or call specific methods."
        ),
    )
    model_id = fields.Many2one(
        comodel_name="ir.model",
        required=True,
        ondelete="cascade",
        help="The Odoo model this field mapping applies to.",
    )
    source_field_id = fields.Many2one(
        string="SAAS Field",
        comodel_name="ir.model.fields",
        domain="[('model_id', '=', model_id)]",
        ondelete="cascade",
        help="The field from the SAAS system that will be mapped to the local system.",
    )
    source_field_name = fields.Char(
        string="SAAS Field Name",
        help="Technical name of the field in the SAAS system.",
    )
    source_field_type = fields.Selection(
        related="source_field_id.ttype",
        string="SAAS Field Type",
        store=True,
        help="The data type of the field in the SAAS system.",
    )
    target_field_id = fields.Many2one(
        string="Local Field",
        comodel_name="ir.model.fields",
        domain="[('model_id', '=', model_id)]",
        ondelete="cascade",
        help=(
            "The corresponding field in the"
            " local Odoo system to map the SAAS field to."
        ),
    )
    target_field_name = fields.Char(
        string="Local Field Name",
        help="Technical name of the field in the local Odoo system.",
    )
    model_name = fields.Char(
        related="model_id.model",
        store=True,
        string="Model Name",
        help="Technical name of the Odoo model (e.g., 'res.partner').",
    )
    is_domain_field = fields.Boolean(
        help=(
            "When enabled, this field will be used in the domain to identify existing "
            "records during synchronization."
        ),
    )
    context = fields.Char(
        default="{}",
        help=(
            "Additional context information in "
            "JSON format for field mapping operations. "
            "This can be used to pass "
            "additional parameters to the field mapping."
        ),
    )
    use_in_create = fields.Boolean(
        default=True,
        help=(
            "Include this field when creating " "new records during synchronization."
        ),
    )
    use_in_write = fields.Boolean(
        default=False,
        help=(
            "Include this field when updating "
            "existing records during synchronization."
        ),
    )
    active = fields.Boolean(
        default=True,
        help="If unchecked, this field mapping will not be used in synchronization.",
    )
    apply_for_root_model = fields.Boolean(
        default=True,
        help=(
            "When enabled, this field mapping will be applied to the main model "
            "being synchronized."
        ),
    )
    apply_for_relation_model = fields.Boolean(
        default=True,
        help=(
            "When enabled, this field mapping will be applied to any relation "
            "models from the field of the root model."
        ),
    )
    related_field_ids = fields.Many2many(
        comodel_name="foreg.o2o.request.field",
        relation="foreg_o2o_request_field_related_field_rel",
        column1="field_id",
        column2="related_field_id",
        domain="[('id', 'in', domain_related_field_ids)]",
        help=(
            "Select related fields that should be synchronized together with this "
            "field. Only fields that reference the current model will be available "
            "for selection."
        ),
    )
    domain_related_field_ids = fields.Many2many(
        compute="_compute_domain_related_field_ids",
        comodel_name="foreg.o2o.request.field",
        relation="foreg_o2o_request_field_domain_related_field_rel",
        column1="field_id",
        column2="domain_related_field_id",
        help=(
            "Technical field that computes the available related fields based on "
            "the current model's relationships."
        ),
    )

    @api.depends("model_id", "source_field_name", "target_field_name")
    def _compute_name(self):
        """Compute the display name for the field mapping.

        This method creates a human-readable name showing the model,
        source field, and target field for easy identification.

        Example:
            >>> field._compute_name()
            >>> print(field.name)  # Output: 'Res Partner: name -> display_name'
        """
        for rec in self:
            rec.name = (
                f"{rec.model_id.name}: "
                f"{rec.source_field_name} -> {rec.target_field_name}"
            )

    @api.depends("model_id")
    def _compute_domain_related_field_ids(self):
        """Compute available related fields for domain filtering.

        This method identifies fields that can be used as related fields
        based on the current model's relationships and field definitions.

        Example:
            >>> field._compute_domain_related_field_ids()
            >>> print(field.domain_related_field_ids)
        """
        for rec in self:
            current_field_model = rec.model_id.model
            rec.domain_related_field_ids = rec.request_id.field_ids.filtered(
                lambda x, cfm=current_field_model, r=rec: x.model_id
                and r.source_field_name in r.env[x.model_id.model]._fields
                and isinstance(
                    r.env[x.model_id.model][r.source_field_name],
                    models.Model,
                )
                and r.env[x.model_id.model][r.source_field_name]._name == cfm
            )

    @api.onchange("request_id")
    def _onchange_request_id(self):
        """Update model_id when request_id changes.

        This method automatically sets the model_id based on the
        selected request's model configuration.

        Example:
            >>> field._onchange_request_id()
        """
        self.model_id = self.request_id.model_id

    @api.onchange("model_id")
    def _onchange_model_id(self):
        """Reset source_field_id when model_id changes.

        This method clears the source field selection when the model
        changes to ensure field compatibility.

        Example:
            >>> field._onchange_model_id()
        """
        self.source_field_id = False

    @api.onchange("source_field_id")
    def _onchange_source_field_id(self):
        """Update source field name and auto-set target field.

        This method updates the source field name and automatically
        sets the target field to the same field if not already set.

        Example:
            >>> field._onchange_source_field_id()
        """
        self.source_field_name = self.source_field_id.name
        if self.source_field_id and not self.target_field_id:
            self.target_field_id = self.source_field_id

    @api.onchange("target_field_id")
    def _onchange_target_field_id(self):
        """Update target field name when target field changes.

        This method automatically updates the target field name
        based on the selected target field.

        Example:
            >>> field._onchange_target_field_id()
        """
        self.target_field_name = self.target_field_id.name

    def get_map_field_dict(self, inverse=False):
        """Get field mapping dictionary for synchronization.

        This method creates a dictionary mapping source fields to target
        fields, organized by model name for easy lookup during sync.

        Args:
            inverse (bool, optional): If True, reverse the mapping direction.
                Defaults to False.

        Returns:
            dict: Field mapping dictionary organized by model

        Example:
            >>> mappings = field.get_map_field_dict()
            >>> print(mappings.get('res.partner', {}))
        """
        result = {}
        for rec in self:
            if inverse:
                result.setdefault(rec.model_name, {}).update(
                    {rec.target_field_name: rec.source_field_name}
                )
            else:
                result.setdefault(rec.model_name, {}).update(
                    {rec.source_field_name: rec.target_field_name}
                )
        return result

    def get_domain_field_dict(self):
        """Get domain field dictionary for filtering.

        This method creates a dictionary of fields that are marked
        as domain fields, organized by model name for filtering operations.

        Returns:
            dict: Domain field dictionary organized by model

        Example:
            >>> domain_fields = field.get_domain_field_dict()
            >>> print(domain_fields.get('res.partner', []))
        """
        result = {}
        for rec in self:
            if rec.is_domain_field:
                result.setdefault(rec.model_name, []).append(rec.target_field_name)
        return result

    def action_open_form(self):
        """Open the field mapping form in a new window.

        This method opens a form view for editing the current
        field mapping record in a new popup window.

        Returns:
            dict: Action window definition for the form view

        Example:
            >>> action = field.action_open_form()
        """
        return {
            "type": "ir.actions.act_window",
            "res_model": "foreg.o2o.request.field",
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
        }
