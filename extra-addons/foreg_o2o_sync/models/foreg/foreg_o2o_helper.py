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

import logging

from odoo import _, api, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools.json import scriptsafe as json_scriptsafe
from odoo.tools.safe_eval import safe_eval

_logger = logging.getLogger(__name__)


class ForegO2OHelper(models.AbstractModel):
    """4EG O2O Helper for code execution and text processing.

    This abstract model provides utility methods for O2O synchronization
    operations, including Python code execution and text analysis
    capabilities.
    """

    _name = "foreg.o2o.helper"
    _description = "4EG O2O Helper"

    @staticmethod
    def text_contains_code(text):
        """Check if text contains executable Python code.

        This method analyzes text to determine if it contains non-comment
        Python code lines. It filters out empty lines and comment-only lines.

        Args:
            text (str): Text to analyze for code content

        Returns:
            bool: True if text contains executable code, False otherwise

        Example:
            >>> helper = self.env['foreg.o2o.helper']
            >>> helper.text_contains_code("# This is a comment")
            False
            >>> helper.text_contains_code("print('Hello World')")
            True
        """
        if not text:
            return False
        return any(
            line.strip() and not line.strip().startswith("#")
            for line in text.splitlines()
        )

    @api.model
    def compute_python_code(self, local_dict, python_code=False):
        """Execute Python code in a safe environment.

        This method executes Python code within a controlled environment
        with predefined variables and error handling. It provides access
        to common Odoo objects and utilities.

        Args:
            local_dict (dict): Dictionary containing local variables for
                code execution
            python_code (str, optional): Python code to execute

        Returns:
            any: Result value from code execution, if any

        Raises:
            ValidationError: When there is an error in the Python code

        Example:
            >>> helper = self.env['foreg.o2o.helper']
            >>> local_vars = {'data': [1, 2, 3]}
            >>> result = helper.compute_python_code(
            ...     local_vars, "result = sum(data)"
            ... )
            >>> print(result)  # Output: 6
        """
        local_dict.update(
            {
                "helper": self.env["foreg.o2o.helper"],
                "env": self.env,
                "json": json_scriptsafe,
                "UserError": UserError,
                "ValidationError": ValidationError,
                "log": _logger,
                **self.env["ir.actions.actions"]._get_eval_context(),
            }
        )
        try:
            safe_eval(python_code, local_dict, mode="exec", nocopy=True)
            return local_dict.get("result")
        except Exception as ex:
            raise ValidationError(
                _(
                    """
Wrong python code defined.
Here is the error received:

%(err)s
                    """,
                    err=repr(ex),
                )
            ) from ex
