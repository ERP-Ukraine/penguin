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

from .foreg_webhook import STANDARD_DEFAULT_PYTHON_CODE


class ForegWebhookCodeTemplate(models.Model):
    _name = "foreg.webhook.code.template"
    _description = "4EG Webhook Code Template"

    name = fields.Char(
        required=True,
        help="Name of the code template",
    )
    description = fields.Text(
        help="Description of the code template",
    )
    code = fields.Text(
        help="Code of the code template",
        default=STANDARD_DEFAULT_PYTHON_CODE,
    )
    active = fields.Boolean(
        default=True,
        help="Whether the code template is active",
    )
