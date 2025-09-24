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


class ForegO2OWorkflow(models.Model):
    _name = "foreg.o2o.workflow"
    _description = "4EG O2O Workflow"

    name = fields.Char(help="Name of the workflow")
    active = fields.Boolean(
        default=True,
        help="If unchecked, the workflow will be archived and hidden from list views",
    )
    description = fields.Text(
        help="Detailed description of the workflow's purpose and functionality"
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        default=lambda self: self.env.company,
        required=True,
        help="Company this workflow belongs to",
    )
    job_ids = fields.One2many(
        comodel_name="foreg.o2o.workflow.job",
        inverse_name="workflow_id",
        string="Jobs",
        help="List of jobs in this workflow",
    )
    cron_ids = fields.One2many(
        comodel_name="ir.cron",
        inverse_name="o2o_workflow_id",
        string="Crons",
        help="Scheduled actions related to this workflow",
    )

    def compute_values_python_code(self, job, python_script):
        """Execute Python code with proper workflow context and variables.

        Provides a secure execution environment for Python scripts within
        the workflow context, including access to job data, workflow instance,
        and input JSON. Uses the foreg.o2o.helper service for safe code execution
        with predefined local variables.

        Args:
            job (recordset): The workflow job record providing execution context
            python_script (str): Python code string to execute within the context

        Returns:
            dict: Result dictionary from the executed Python code, containing
                the outcome and any computed values

        Example:
            >>> script = "result = {'status': 'success', 'value': job.name}"
            >>> result = self.compute_values_python_code(job_record, script)
            >>> print(result['status'])
            'success'
        """
        self.ensure_one()
        localdict = {
            "job": job,
            "workflow": self,
            "result": False,
            "input_json": job.input_json,
        }

        return self.env["foreg.o2o.helper"].compute_python_code(
            localdict, python_script
        )

    def action_run_workflow(self):
        """Execute the complete workflow by running all active jobs in sequence.

        Orchestrates the execution of all active jobs within the workflow,
        respecting their execution conditions and dependency relationships.
        Jobs are processed based on their execute_by criteria (sequence,
        job completion status, or Python script conditions). Handles error
        management and state tracking for each job execution.

        Returns:
            bool: True when workflow execution is completed (regardless of
                individual job success/failure states)

        Raises:
            No exceptions are raised; errors are captured in job states and
            output JSON for individual jobs

        Example:
            >>> workflow = self.env['foreg.o2o.workflow'].browse(workflow_id)
            >>> result = workflow.action_run_workflow()
            >>> print("Workflow execution completed")
        """
        self.ensure_one()

        # Get all active jobs ordered by sequence and creation date
        sequence_jobs = self.job_ids.filtered(lambda j: j.active).sorted(
            key=lambda j: (j.sequence, j.create_date)
        )
        input_json = {}
        for job in sequence_jobs:
            # Skip jobs that don't have a valid action configuration
            job.input_json = input_json
            if job.action_type not in ["send_request", "call_webhook", "python_script"]:
                continue

            # Skip request jobs without request_id
            if job.action_type == "send_request" and not job.request_id:
                continue

            # Record start time
            job.datetime_start = fields.Datetime.now()
            should_execute = False

            # Determine if job should be executed based on execute_by condition
            if job.execute_by == "sequence":
                should_execute = True
            elif (
                job.execute_by == "job_done"
                and job.job_id
                and job.job_id.state == "done"
            ):
                should_execute = True
            elif (
                job.execute_by == "job_failed"
                and job.job_id
                and job.job_id.state == "failed"
            ):
                should_execute = True
            elif job.execute_by == "python_script" and job.execute_by_python_script:
                try:
                    # Execute the python script to determine if job should run
                    result_dict = self.compute_values_python_code(
                        job, job.execute_by_python_script
                    )
                    should_execute = bool(result_dict)
                except Exception as e:
                    job.state = "failed"
                    input_json = {
                        "result": "failed",
                        "error": str(e),
                    }
                    job.output_json = input_json
                    job.datetime_end = fields.Datetime.now()
                    continue

            # Execute job if conditions are met
            if should_execute:
                try:
                    # Run the job's action
                    job.action_run_job()
                    input_json = job.output_json
                except Exception as e:
                    job.state = "failed"
                    input_json = {
                        "result": "failed",
                        "error": str(e),
                    }
                    job.output_json = input_json
                    job.datetime_end = fields.Datetime.now()
            else:
                job.state = "cancelled"
                input_json = {
                    "result": "cancelled",
                    "reason": "Job execution conditions not met",
                }
                job.output_json = input_json
                job.datetime_end = fields.Datetime.now()

        return True

    def action_generate_cron(self):
        """Generate a scheduled cron job to automatically run this workflow.

        Creates a new scheduled action (cron job) that will automatically
        execute this workflow at regular intervals. The cron job is configured
        with default settings for daily execution and includes proper user
        context and workflow reference.

        Returns:
            recordset: The created ir.cron record representing the scheduled
                action for this workflow

        Example:
            >>> workflow = self.env['foreg.o2o.workflow'].browse(workflow_id)
            >>> cron_job = workflow.action_generate_cron()
            >>> print(f"Created cron job: {cron_job.name}")
        """
        self.ensure_one()
        # Create cron job for this workflow
        cron_data = {
            "name": f"Run Workflow: {self.name}",
            "model_id": self.env["ir.model"].search([("model", "=", self._name)]).id,
            "state": "code",
            "code": f"model.browse({self.id}).action_run_workflow()",
            "user_id": self.env.user.id,
            "interval_number": 1,
            "interval_type": "days",
            "active": True,
            "o2o_workflow_id": self.id,
        }

        cron = self.env["ir.cron"].sudo().create(cron_data)
        return cron
