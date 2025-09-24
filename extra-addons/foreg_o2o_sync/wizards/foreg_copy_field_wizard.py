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
from odoo import _, fields, models
from odoo.exceptions import UserError


class ForegCopyFieldWizard(models.TransientModel):
    """4EG Copy Field Wizard for field replication across models.

    This wizard allows users to copy fields from one model to multiple other
    models, facilitating field replication across the system for consistency
    and standardization.
    """

    _name = "foreg.copy.field.wizard"
    _description = "4EG Copy Field Wizard"

    field_id = fields.Many2one(
        comodel_name="ir.model.fields",
        string="Field",
        readonly=True,
        required=True,
        help="Field to copy",
    )
    field_type = fields.Selection(
        related="field_id.ttype",
        help="Type of the field to copy",
    )
    model_id = fields.Many2one(
        comodel_name="ir.model",
        string="Model",
        related="field_id.model_id",
        help="Model of the field to copy",
    )
    apply_model_ids = fields.Many2many(
        comodel_name="ir.model",
        string="Apply to Models",
        domain='[("id", "!=", model_id)]',
        help="Models to copy the field to",
    )

    def action_apply(self):
        """Apply field copying to selected models.

        This method copies the selected field to all target models specified
        in apply_model_ids. It checks for field name conflicts before copying
        and raises an error if a field with the same name already exists.

        Returns:
            None: No return value

        Raises:
            UserError: When a field with the same name already exists in
                one of the target models

        Example:
            >>> wizard = self.create({
            ...     'field_id': field_record.id,
            ...     'apply_model_ids': [(6, 0, [model1.id, model2.id])]
            ... })
            >>> wizard.action_apply()
        """
        self.ensure_one()
        for model in self.apply_model_ids:
            if self.field_id.name in model.field_id.mapped("name"):
                raise UserError(
                    _(
                        "Field %(field_description)s already "
                        "exists in model %(model_name)s",
                        field_description=self.field_id.field_description,
                        model_name=model.name,
                    )
                )
            self.field_id.copy(
                {
                    "model_id": model.id,
                }
            )
