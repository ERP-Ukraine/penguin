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
import json

from odoo import api, fields, models


class ForegO2OWorkflowJob(models.Model):
    _name = "foreg.o2o.workflow.job"
    _description = "4EG O2O Workflow Job"

    name = fields.Char(help="Name of the workflow job", required=True)
    sequence = fields.Integer(
        default=10, help="Determines the order of execution for jobs"
    )
    active = fields.Boolean(
        default=True,
        help="If unchecked, this job will be archived and hidden from list views",
    )
    job_id = fields.Many2one(
        comodel_name="foreg.o2o.workflow.job",
        help="Related job that triggers this job's execution",
    )
    workflow_id = fields.Many2one(
        comodel_name="foreg.o2o.workflow",
        help="Workflow this job belongs to",
        required=True,
        ondelete="cascade",
    )
    instance_id = fields.Many2one(
        comodel_name="foreg.o2o.instance",
        help="Integration instance for this job",
    )
    execute_by = fields.Selection(
        selection=[
            ("sequence", "Sequence Order"),
            ("job_done", "Job Done"),
            ("job_failed", "Job Failed"),
            ("python_script", "Python Script"),
        ],
        help="Determines how this job is triggered to execute",
        required=True,
        default="sequence",
    )
    execute_by_python_script = fields.Text(
        string="Trigger Condition",
        help="Python script to execute for determining when this job should run",
        default="""
# Execute python code, result = True will execute the job
# Ex: result = {}
# Common variables
#  - env: Odoo Environment on which the action is triggered
#  - input_json: input JSON of the job
#  - user: current res.user
#  - job: current job
#  - workflow: current workflow
#  - helper: current foreg.o2o.helper
# Python lib:
#  - datetime
#  - json
#  - time
#  - dateutil
#  - timezone
#  - b64encode
#  - b64decode
""",
    )
    output_json = fields.Json(
        help="Output JSON of the job",
        default="{}",
    )
    input_json = fields.Json(
        help="Input JSON of the job",
        default="{}",
    )
    input_json_display = fields.Text(
        compute="_compute_input_json_display",
        help="Input JSON of the job",
        default="{}",
    )
    output_json_display = fields.Text(
        compute="_compute_output_json_display",
        help="Output JSON of the job",
        default="{}",
    )

    action_type = fields.Selection(
        selection=[
            ("send_request", "Send Request"),
            ("call_webhook", "Call Webhook"),
            ("python_script", "Python Script"),
        ],
        help="Type of action to be performed by this job",
        required=True,
        default="send_request",
    )
    action_python_script = fields.Text(
        string="Action Script",
        help="Python script to execute when this job runs",
        default="""
# Ex: result = {}
# Common variables
#  - env: Odoo Environment on which the action is triggered
#  - user: current res.user
#  - input_json: input JSON of the job
#  - job: current job
#  - workflow: current workflow
#  - helper: current foreg.o2o.helper
# Python lib:
#  - datetime
#  - json
#  - time
#  - dateutil
#  - timezone
#  - b64encode
#  - b64decode
""",
    )
    request_id = fields.Many2one(
        comodel_name="foreg.o2o.request",
        domain="[('instance_id', '=', instance_id)]",
        help="API request configuration for this job",
    )
    webhook_url = fields.Char(
        help="Webhook URL for this job",
    )
    datetime_start = fields.Datetime(
        string="Start Time", help="When this job started execution"
    )
    datetime_end = fields.Datetime(
        string="End Time", help="When this job finished execution"
    )
    duration = fields.Float(
        compute="_compute_duration",
        store=True,
        digits=(16, 2),
        help="Duration in seconds between start and end time",
    )
    state = fields.Selection(
        selection=[
            ("pending", "Pending"),
            ("done", "Done"),
            ("failed", "Failed"),
            ("cancelled", "Cancelled"),
        ],
        default="pending",
        help="Current status of the job",
    )

    @api.depends("datetime_start", "datetime_end")
    def _compute_duration(self):
        """Compute job execution duration in seconds.

        Calculates the time difference between job start and end timestamps
        to determine how long the job took to execute. Duration is expressed
        in seconds for easy comparison and monitoring of job performance.

        Example:
            >>> job.datetime_start = datetime(2024, 1, 1, 10, 0, 0)
            >>> job.datetime_end = datetime(2024, 1, 1, 10, 0, 30)
            >>> job._compute_duration()
            >>> print(job.duration)
            30
        """
        for record in self:
            duration = 0
            if record.datetime_start and record.datetime_end:
                duration = record.datetime_end - record.datetime_start
            record.duration = duration.seconds if duration else 0

    @api.depends("input_json")
    def _compute_input_json_display(self):
        """Compute formatted display version of input JSON data.

        Converts the input_json field into a human-readable formatted string
        with proper indentation for better visualization in the user interface.
        This computed field is used for display purposes only.

        Example:
            >>> job.input_json = {'key': 'value', 'data': [1, 2, 3]}
            >>> job._compute_input_json_display()
            >>> print(job.input_json_display)
            {
                "key": "value",
                "data": [1, 2, 3]
            }
        """
        for record in self:
            record.input_json_display = json.dumps(record.input_json, indent=4)

    @api.depends("output_json")
    def _compute_output_json_display(self):
        """Compute formatted display version of output JSON data.

        Converts the output_json field into a human-readable formatted string
        with proper indentation for better visualization in the user interface.
        This computed field is used for display purposes only and shows
        the results of job execution.

        Example:
            >>> job.output_json = {'result': True, 'status': 'completed'}
            >>> job._compute_output_json_display()
            >>> print(job.output_json_display)
            {
                "result": true,
                "status": "completed"
            }
        """
        for record in self:
            record.output_json_display = json.dumps(record.output_json, indent=4)

    def action_run_job(self):
        """Execute this job's action based on its configured action type.

        Performs the job execution according to the action_type configuration:
        - send_request: Executes the associated O2O request
        - call_webhook: Sends HTTP POST request to specified webhook URL
        - python_script: Executes custom Python code within workflow context

        Handles timing, state management, error handling, and result capture
        for all action types. Always records execution start/end times and
        updates job state based on execution outcome.

        Returns:
            bool: Always returns True to indicate the execution attempt
                completed (actual success/failure is tracked in job state)

        Example:
            >>> job = self.env['foreg.o2o.workflow.job'].browse(job_id)
            >>> result = job.action_run_job()
            >>> print(f"Job state: {job.state}")
            'done' or 'failed'
        """
        self.ensure_one()
        self.datetime_start = fields.Datetime.now()

        try:
            if self.action_type == "send_request" and self.request_id:
                # Execute request
                last_log = self.request_id.action_send_request(return_request_log=True)

                # Get the last log (logs are ordered by create_date desc)
                if last_log:
                    if last_log.state == "pass":
                        self.state = "done"
                        self.output_json = {
                            "result": True,
                            "request_log_id": last_log.id,
                        }
                    else:
                        self.state = "failed"
                        self.output_json = {
                            "result": False,
                            "request_log_id": last_log.id,
                        }
                else:
                    self.state = "failed"
                    self.output_json = {
                        "result": False,
                        "error": "No log records found after request execution",
                    }

            elif self.action_type == "call_webhook" and self.webhook_url:
                # Import requests library only when needed
                import requests

                # Prepare payload for webhook
                payload = {
                    "instance_id": self.instance_id.id,
                    "job_id": self.id,
                    "workflow_id": self.workflow_id.id,
                    "input_json": self.input_json,
                    "url": self.env["ir.config_parameter"]
                    .sudo()
                    .get_param("web.base.url"),
                }

                # Send webhook request
                response = requests.post(self.webhook_url, json=payload, timeout=30)

                # Process response
                if response.status_code == 200:
                    self.state = "done"
                    self.output_json = {
                        "status_code": response.status_code,
                        "response": response.text,
                    }
                else:
                    self.state = "failed"
                    self.output_json = {
                        "status_code": response.status_code,
                        "response": response.text,
                    }

            elif self.action_type == "python_script" and self.action_python_script:
                # Execute python script
                result = self.workflow_id.compute_values_python_code(
                    self, self.action_python_script
                )

                # Process result
                if result:
                    self.state = "done"
                    self.output_json = {
                        "result": result,
                    }
                else:
                    self.state = "failed"
                    self.output_json = {
                        "result": result,
                    }
            else:
                self.state = "failed"
                self.output_json = {
                    "result": False,
                    "error": "Invalid action configuration",
                }

        except Exception as e:
            self.state = "failed"
            self.output_json = {
                "result": "Failed",
                "error": str(e),
            }

        finally:
            # Always record end time
            self.datetime_end = fields.Datetime.now()

        return True
