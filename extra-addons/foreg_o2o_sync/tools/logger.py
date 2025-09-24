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

from odoo import fields
from odoo.tools import plaintext2html


class Logger:
    """Custom logger for O2O synchronization operations.

    This logger provides enhanced logging functionality with HTML formatting
    and color-coded log levels. It maintains an internal log buffer and
    provides methods to retrieve formatted logs.
    """

    def __init__(self):
        """Initialize the logger with an empty log buffer.

        Creates a new Logger instance with an empty list to store log messages.
        """
        self.logs = []

    def __bool__(self):
        """Return True to indicate the logger is always available.

        Returns:
            bool: Always returns True
        """
        return True

    def info(self, msg, *args):
        """Log an informational message.

        Args:
            msg (str): The message to log
            *args: Format arguments for the message

        Example:
            >>> logger.info("Operation completed successfully")
            >>> logger.info("Processed %d records", 10)
        """
        self._log(logging.INFO, msg, *args)

    def warning(self, msg, *args):
        """Log a warning message.

        Args:
            msg (str): The warning message to log
            *args: Format arguments for the message

        Example:
            >>> logger.warning("Field %s not found", "name")
        """
        self._log(logging.WARNING, msg, *args)

    def error(self, msg, *args):
        """Log an error message.

        Args:
            msg (str): The error message to log
            *args: Format arguments for the message

        Example:
            >>> logger.error("Failed to connect to instance %s", instance_name)
        """
        self._log(logging.ERROR, msg, *args)

    def title(self, title):
        """Log a title with visual separation.

        Args:
            title (str): The title text to display

        Example:
            >>> logger.title("Starting Import Process")
        """
        logging.info("\n\n" + "=" * 88 + "\n" + title + "\n" + "=" * 88)

    def _log(self, level, msg, *args):
        """Internal method to handle logging and HTML formatting.

        This method processes the message, formats it with arguments if provided,
        and stores it in the internal log buffer with HTML formatting and
        color-coded log levels.

        Args:
            level (int): Logging level (INFO, WARNING, ERROR)
            msg (str): The message to log
            *args: Format arguments for the message

        Example:
            >>> self._log(logging.INFO, "Processing %s", "data")
        """
        logging.log(level, msg, *args)
        level_color_dict = {
            logging.INFO: '<span style="color:green">INFO</span>',
            logging.WARNING: '<span style="color:darkorange">WARNING</span>',
            logging.ERROR: '<span style="color:red">ERROR</span>',
        }

        if isinstance(msg, str) and args:
            msg = msg % args
        if "\n" in str(msg):
            msg = plaintext2html(str(msg))
        self.logs.append(
            "<p>{now} - {level_color} {msg}</p>".format(
                now=fields.Datetime.now(),
                level_color=level_color_dict.get(level, "red"),
                msg=msg,
            )
        )

    def get_logs(self):
        """Retrieve all logged messages as HTML.

        Returns:
            str: HTML-formatted string containing all logged messages

        Example:
            >>> html_logs = logger.get_logs()
            >>> print(html_logs)
        """
        return "".join(self.logs)
