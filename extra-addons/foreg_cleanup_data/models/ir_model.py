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

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools.safe_eval import safe_eval, test_python_expr

from odoo.addons.base.models.ir_actions import LoggerProxy

_logger = logging.getLogger(__name__)


class IrModel(models.Model):
    """Extension of ir.model for data cleanup functionality."""

    _inherit = "ir.model"

    enable_cleanup = fields.Boolean(
        string="Enable Autocleanup",
        help="Enable automatic cleanup of records based on configured domain",
    )
    cleanup_domain_type = fields.Selection(
        selection=[("fixed", "Fixed"), ("code", "Code")],
        default="fixed",
        string="Domain Type",
        help="Type of domain to use for filtering records to clean up",
    )
    cleanup_fixed_domain = fields.Text(
        string="Fixed Domain",
        help=(
            "Domain expression to filter records for cleanup (e.g., "
            "[('create_date', '<', datetime.now())])"
        ),
    )
    cleanup_code_domain = fields.Text(
        string="Python Code Domain",
        help="Python code that returns a domain list to filter records for cleanup",
    )
    cleanup_batch_size = fields.Integer(
        default=1000,
        string="Batch Size",
        help="Number of records to delete in a single batch",
    )
    cleanup_batch_count = fields.Integer(
        default=10,
        string="Batch Count",
        help="Maximum number of batches to process in a single run",
    )
    cleanup_order = fields.Selection(
        selection=[("id_asc", "ID Ascending"), ("id_desc", "ID Descending")],
        default="id_asc",
        help="Order in which records will be selected for cleanup",
    )

    @api.constrains("cleanup_code_domain")
    def _check_python_code(self):
        """Validate that the Python code domain is syntactically correct.

        This constraint checks the syntax of the Python code provided in the
        cleanup_code_domain field. If the code is invalid, a ValidationError
        is raised to prevent saving the record.
        """
        for model in self.sudo().filtered("cleanup_code_domain"):
            msg = test_python_expr(expr=model.cleanup_code_domain.strip(), mode="exec")
            if msg:
                raise ValidationError(msg)

    def action_view_cron(self):
        """Open the scheduled actions (cron jobs) related to cleanup.

        This method returns an action that opens the scheduled actions view,
        filtered to show cleanup cron jobs related to this model.

        Returns:
            dict: Action to open the scheduled actions view filtered to show
                cleanup cron jobs.
        """
        self.ensure_one()

        # Find the cleanup cron job
        cleanup_cron = self.env.ref(
            "foreg_cleanup_data.4eg_ir_model_cleanup_data_cron", False
        )
        if cleanup_cron:
            return cleanup_cron.with_context(create=False)._get_records_action()

    def _get_domain_from_config(self):
        """Get domain from configuration (fixed or code type).

        This method determines the domain to use for cleanup based on the
        configuration. It supports both fixed domain expressions and Python
        code domains. If the domain type is 'fixed', it evaluates the domain
        expression. If the domain type is 'code', it executes the Python code
        to obtain the domain.

        Returns:
            list: Domain expression for filtering records.

        Raises:
            UserError: If there's an issue evaluating the domain.
        """
        self.ensure_one()

        def log(message, level="info"):
            """Log messages to ir.logging table.

            Args:
                message (str): Message to log
                level (str): Log level (default: "info")
            """
            with self.pool.cursor() as cr:
                query = (
                    "INSERT INTO ir_logging(create_date, create_uid, type, "
                    "dbname, name, level, message, path, line, func) "
                    "VALUES (NOW() at time zone 'UTC', %s, %s, %s, "
                    "%s, %s, %s, %s, %s, %s)"
                )
                cr.execute(
                    query,
                    (
                        self.env.uid,
                        "client",
                        self._cr.dbname,
                        __name__,
                        level,
                        message,
                        "model",
                        self.id,
                        self.name,
                    ),
                )

        try:
            if self.cleanup_domain_type == "fixed":
                cleanup_fixed_domain = (
                    self.cleanup_fixed_domain.strip()
                    if self.cleanup_fixed_domain
                    else "[]"
                )
                return safe_eval(cleanup_fixed_domain, {}, mode="eval", nocopy=True)
            else:
                eval_context = self.env["ir.actions.actions"]._get_eval_context()
                eval_context.update(
                    {
                        "env": self.env,
                        "model": self.model,
                        "UserError": UserError,
                        "log": log,
                        "_logger": LoggerProxy,
                        "domain": [],
                    }
                )
                cleanup_code_domain = (
                    self.cleanup_code_domain.strip()
                    if self.cleanup_code_domain
                    else "domain = []"
                )
                safe_eval(cleanup_code_domain, eval_context, mode="exec", nocopy=True)
                return eval_context.get("domain", [])
        except Exception as e:
            raise UserError(
                f"Error evaluating domain for model {self.name}: {str(e)}"
            ) from e

    def action_preview_cleanup_domain(self):
        """Preview the domain and affected records.

        This method previews the domain that will be used for cleanup and
        counts the number of records that would be affected. It returns a
        notification action displaying the domain and the affected record
        count, or an error notification if evaluation fails.

        Returns:
            dict: Action showing notification with domain and affected record
                count or error message.
        """
        self.ensure_one()
        try:
            domain = self._get_domain_from_config()
            target_model = self.env[self.model]
            len_records = target_model.search_count(domain)
            self._cr.rollback()

            return self._get_notification_action(
                "Domain Preview",
                f"Domain: {domain}\nAffected records: {len_records}",
                "info",
                False,
            )
        except Exception as e:
            self._cr.rollback()
            return self._get_notification_action("Error", str(e), "danger", True)

    def _get_notification_action(self, title, message, type_="info", sticky=False):
        """Helper method to create notification action.

        This helper constructs a client action for displaying a notification
        in the Odoo UI.

        Args:
            title (str): Notification title.
            message (str): Notification message.
            type_ (str): Notification type (info, warning, danger).
            sticky (bool): Whether notification should be sticky.

        Returns:
            dict: Client action for notification.
        """
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": title,
                "message": message,
                "sticky": sticky,
                "type": type_,
            },
        }

    def _cron_general_cleanup_records(self):
        """Scheduled action for cleaning up records based on configured domains.

        This method is called by the scheduled cron job to delete records
        that match the specified domain for each enabled model. It iterates
        over all models with cleanup enabled and triggers the cleanup process
        for each.
        """
        cleanup_models = self.search([("enable_cleanup", "=", True)])

        if not cleanup_models:
            _logger.info("No models configured for cleanup")
            return

        for model in cleanup_models:
            self._cleanup_model_records(model)

    def _cleanup_model_records(self, model):
        """Clean up records for a specific model.

        This method deletes records for the given model in batches, according
        to the cleanup configuration. It logs progress and errors for each
        batch. Records are deleted in the order specified by the configuration.

        Args:
            model (ir.model): Model record containing cleanup configuration.
        """
        try:
            _logger.info("Starting cleanup for model: %s", model.model)
            list_domain = model._get_domain_from_config()
            target_model = self.env[model.model]
            batch_size = model.cleanup_batch_size
            batch_count = model.cleanup_batch_count
            deleted_count = 0

            # Get the actual cleanup order string from the selection field
            cleanup_order = model.cleanup_order.replace("_", " ")

            # Delete records in batches
            records = target_model.with_context(active_test=False).search(
                list_domain, limit=batch_size * batch_count, order=cleanup_order
            )

            if not records:
                _logger.info("No records to cleanup for model: %s", model.model)
                return

            total_batches = (len(records) - 1) // batch_size + 1

            for count in range(0, len(records), batch_size):
                batch = records[count : count + batch_size]
                current_batch = (count // batch_size) + 1

                try:
                    if not batch.exists():
                        continue

                    batch_size_actual = len(batch)
                    batch.unlink()
                    self.env.cr.commit()  # pylint: disable=invalid-commit
                    deleted_count += batch_size_actual

                    _logger.info(
                        "Batch %s/%s: Deleted %s records of %s (Total: %s)",
                        current_batch,
                        total_batches,
                        batch_size_actual,
                        model.model,
                        deleted_count,
                    )
                except Exception as e:
                    self.env.cr.rollback()
                    _logger.error(
                        "Failed to delete batch %s/%s records of %s: %s",
                        current_batch,
                        total_batches,
                        model.model,
                        str(e),
                    )

            _logger.info(
                "Cleanup completed for %s: Deleted %s records",
                model.model,
                deleted_count,
            )
        except Exception as e:
            _logger.error("Error during cleanup of model %s: %s", model.model, str(e))
