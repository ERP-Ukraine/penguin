# -*- coding: utf-8 -*-
#!/usr/bin/python3
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import models, fields, api


class GetProductStatusQueue(models.Model):
    _name = "get.product.status.queue.gcs"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Get Product Status Queue GCS"
    _order = "name desc"
    
    STATE_SELECTION = [
        ('draft', 'Draft'), ('partially_completed', 'Partially Completed'),
        ('completed', 'Completed'), ('failed', 'Failed')
    ]
    
    name = fields.Char(help="name", copy=False)
    gs_instance_id = fields.Many2one('google.shopping.feed.instance', string="Shopping Instance")
    gs_account_id = fields.Many2one("google.shopping.feed.account", related="gs_instance_id.gs_account_id", store=True,
                                    string="Shopping Account", help="Shopping account")
    log_tracker = fields.Many2one('google.shopping.feed.log.tracker', string="Log Tracker")
    log_tracker_lines = fields.One2many(related="log_tracker.gsf_log_line_tracker_ids")
    state = fields.Selection(STATE_SELECTION, tracking=True, default='draft', copy=False,
                             compute="_compute_queue_state", store=True)
    get_product_status_queue_lines = fields.One2many("get.product.status.queue.lines.gcs",
                                                    "get_product_status_queue_id",
                                                    string="Product Status Queue Lines")
    queue_line_total_records = fields.Integer(string="Total Records",
                                              compute="_compute_queue_line_records")
    queue_line_draft_records = fields.Integer(string="Draft Records",
                                              compute="_compute_queue_line_records")
    queue_line_failed_records = fields.Integer(string="Fail Records",
                                             compute="_compute_queue_line_records")
    queue_line_done_records = fields.Integer(string="Done Records",
                                             compute="_compute_queue_line_records")
    queue_line_cancelled_records = fields.Integer(string="Cancelled Records",
                                               compute="_compute_queue_line_records")
    
    @api.depends("get_product_status_queue_lines.state")
    def _compute_queue_state(self):
        for product_queue in self:
            if product_queue.queue_line_total_records == product_queue.queue_line_done_records + \
                    product_queue.queue_line_cancelled_records:
                product_queue.state = "completed"
            elif product_queue.queue_line_total_records == product_queue.queue_line_draft_records:
                product_queue.state = "draft"
            elif product_queue.queue_line_total_records == product_queue.queue_line_failed_records:
                product_queue.state = "failed"
            else:
                product_queue.state = "partially_completed"
    
    @api.depends("get_product_status_queue_lines.state")
    def _compute_queue_line_records(self):
        for product_queue in self:
            queue_lines = product_queue.get_product_status_queue_lines
            product_queue.queue_line_total_records = len(queue_lines)
            product_queue.queue_line_draft_records = len(queue_lines.filtered(lambda x: x.state == "draft"))
            product_queue.queue_line_failed_records = len(queue_lines.filtered(lambda x: x.state == "failed"))
            product_queue.queue_line_done_records = len(queue_lines.filtered(lambda x: x.state == "done"))
            product_queue.queue_line_cancelled_records = len(queue_lines.filtered(lambda x: x.state == "cancel"))
            
    @api.model
    def create(self, vals):
        sequence_id = self.env.ref("google_shopping_feed_gcs.google_shopping_get_product_status_queue_seq").ids
        if sequence_id:
            sequence_name = self.env["ir.sequence"].browse(sequence_id).next_by_id()
        else:
            sequence_name = "/"
        vals.update({"name": sequence_name or ""})
        return super(GetProductStatusQueue, self).create(vals)
    
    def generate_sendone_notification(self, message):
        """
        @author: Grow Consultancy Services
        """
        bus_bus_obj = self.env["bus.bus"]
        bus_bus_obj._sendone(self.env.user.partner_id, "google_shopping_get_product_status_queue_gcs", {
                             "title": "Google Shopping Connector",
                             "message": message, "sticky": False, "warning": True})


class GetProductStatusQueueLines(models.Model):
    _name = "get.product.status.queue.lines.gcs"
    _description = "Get Product Status Queue Line GCS"
    
    STATE_SELECTION = [
        ('draft', 'Draft'), ('failed', 'Failed'),
        ('done', 'Done'), ('cancel', 'Cancelled')
    ]
    
    get_product_status_queue_id = fields.Many2one("get.product.status.queue.gcs", "Queue ID", required=True,
                                                   ondelete="cascade", copy=False)
    gs_instance_id = fields.Many2one('google.shopping.feed.instance',
                                     related="get_product_status_queue_id.gs_instance_id",
                                     store=True,
                                     string="Shopping Instance")
    gs_account_id = fields.Many2one("google.shopping.feed.account", related="gs_instance_id.gs_account_id", store=True,
                                    string="Shopping Account", help="Shopping account")
    synced_product_response = fields.Text("Synced Product Response")
    product_offer_id = fields.Char("Product Offer ID")
    response_status_code = fields.Char("Response Status Code")
    name = fields.Char(string="Product Name", help="Product name")
    state = fields.Selection(STATE_SELECTION, string="State", default='draft', copy=False)
    log_tracker_lines = fields.One2many("google.shopping.feed.log.line.tracker", "get_product_status_queue_line_id",
                                        help="Log tracker lines against particularly queue line")
        
