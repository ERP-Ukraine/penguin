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

from odoo import _, api, models
from odoo.exceptions import UserError
from odoo.osv import expression


class IrModelFields(models.Model):
    """Extended Model Fields for O2O synchronization.

    This model extends the standard model fields to include O2O-specific
    functionality such as automatic field naming conventions and field
    replication capabilities.
    """

    _inherit = "ir.model.fields"

    @api.onchange("name")
    def _onchange_name(self):
        """Handle field name changes for O2O field creation.

        This method automatically formats field names when creating fields
        from O2O context. It ensures proper naming conventions by adding
        'x_' prefix and formatting the field description.

        Example:
            >>> field = self.create({
            ...     'name': 'customer_name',
            ...     'field_description': 'Customer Name'
            ... })
            >>> field.name  # Result: 'x_customer_name'
        """
        if self.env.context.get("create_from_o2o") and (self.name or "x_") != "x_":
            self.field_description = self.name
            self.name = "x_" + self.field_description.lower().replace(" ", "_")

    def action_apply_to_other_models(self):
        """Open wizard to copy field to other models.

        This method opens the field copy wizard to allow users to replicate
        the current field across multiple models. It performs validation
        to ensure the field can be copied.

        Returns:
            dict: Action window definition for the copy field wizard

        Raises:
            UserError: When trying to copy base fields or unsupported field types

        Example:
            >>> field = self.env['ir.model.fields'].browse(1)
            >>> action = field.action_apply_to_other_models()
        """
        self.ensure_one()
        if self.state == "base":
            raise UserError(_("You cannot copy base fields to other models"))
        elif self.ttype in (
            "many2many",
            "one2many",
            "many2one_reference",
            "properties",
            "properties_definition",
            "reference",
            "serialized",
        ):
            raise UserError(
                _("You cannot copy fields of type %s to other models") % self.ttype
            )
        return {
            "type": "ir.actions.act_window",
            "res_model": "foreg.copy.field.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_field_id": self.id,
            },
        }

    @api.model
    def name_search(self, name="", args=None, operator="ilike", limit=100):
        """Enhanced name search with exact match priority for field names.

        This method extends the standard name_search to prioritize exact
        matches when searching for model fields by name. If an exact match
        is found, it returns that result immediately, otherwise falls back
        to the standard search behavior.

        Args:
            name (str, optional): Search term to match against field names.
                Defaults to "".
            args (list, optional): Additional domain constraints for the search.
                Defaults to None.
            operator (str, optional): Search operator to use. Defaults to "ilike".
            limit (int, optional): Maximum number of results to return.
                Defaults to 100.

        Returns:
            list: List of tuples containing (id, display_name) for matching
                records

        Example:
            >>> fields = self.env['ir.model.fields']
            >>> results = fields.name_search("customer_name")
            >>> # Returns exact match first if found, otherwise similar matches
        """
        domain = args or []
        if (
            name
            and operator not in expression.NEGATIVE_TERM_OPERATORS
            and (
                record := self.search_fetch(
                    expression.AND([[("name", "=", name)], domain]), ["display_name"]
                )
            )
        ):
            return [(record.id, record.display_name)]
        return super().name_search(name, domain, operator, limit)
