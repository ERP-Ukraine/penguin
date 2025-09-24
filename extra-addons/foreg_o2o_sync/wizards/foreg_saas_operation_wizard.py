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

from odoo import fields, models


class ForegSaasOperationWizard(models.TransientModel):
    """4EG SaaS Operation Wizard for executing O2O operations.

    This wizard provides a user interface for executing SaaS operations
    through O2O requests. It allows users to select target instances and
    requests, and execute them with optional filters.
    """

    _name = "foreg.saas.operation.wizard"
    _description = "4EG SaaS Operation Wizard"

    saas_instance_id = fields.Many2one(
        comodel_name="foreg.o2o.instance",
        string="Saas Instance",
        required=True,
        default=lambda self: self.env["foreg.o2o.instance"].search([], limit=1),
        help=(
            "Select the SAAS instance to perform operations on. This represents the "
            "target system for the operation."
        ),
    )
    saas_request_id = fields.Many2one(
        comodel_name="foreg.o2o.request",
        string="Saas Request",
        required=True,
        help="Select the SAAS request that defines the operation to be executed.",
    )
    method = fields.Selection(
        related="saas_request_id.method",
        readonly=True,
        help=(
            "The HTTP method to be used for the SAAS operation "
            "(e.g., GET, POST, PUT)."
        ),
    )
    model = fields.Char(
        related="saas_request_id.model",
        readonly=True,
        help="The Odoo model name that this SAAS operation will interact with.",
    )
    read_filter = fields.Char(
        default="[]",
        help=(
            "JSON-formatted domain filter for read operations. Default is '[]' which "
            "matches all records."
        ),
    )

    def execute_saas_operations(self):
        """Execute the selected SaaS operation.

        This method executes the selected SaaS request based on its method type.
        For read operations, it applies the specified filter. For other operations,
        it executes the request without additional parameters.

        Returns:
            bool: True if the operation was executed successfully

        Example:
            >>> wizard = self.create({
            ...     'saas_instance_id': instance.id,
            ...     'saas_request_id': request.id,
            ...     'read_filter': '[("active", "=", True)]'
            ... })
            >>> result = wizard.execute_saas_operations()
        """
        self.ensure_one()
        request = self.saas_request_id
        if request.method == "read":
            request.action_send_request(read_filter=self.read_filter)
        else:
            request.action_send_request()
        return True
