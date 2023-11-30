# -*- coding: utf-8 -*-
#!/usr/bin/python3
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import models, fields, api


class GoogleShoppingFeedLogTracker(models.Model):
    _name = "google.shopping.feed.log.tracker"
    _description = "Google Shopping Feed Log Tracker"
    _order = "id desc"
    
    name = fields.Char("Log Tracker", default="Log", index=True, help="Log tracker ID")
    gs_instance_id = fields.Many2one('google.shopping.feed.instance', string="Shopping Instance")
    gs_account_id = fields.Many2one("google.shopping.feed.account", related="gs_instance_id.gs_account_id", store=True, 
                                    string="Shopping Account", help="Shopping aaccount")
    log_message = fields.Text("Log Message")
    operation_type = fields.Selection([
        ('import', 'Import'), 
        ('export', 'Export'),
        ('update', 'Update'),
        ('delete', 'Delete')
    ], string="Operation Type")
    operation_sub_type = fields.Selection([
        ('export_product', 'Export Product'),
        ('update_product', 'Update Product'),
        ('import_product', 'Import Product'),
        ('delete_product', 'Delete Product')
    ], string="Operation Sub Type")
    is_skip_process = fields.Boolean("Is Skip Process?")
    gsf_log_line_tracker_ids = fields.One2many("google.shopping.feed.log.line.tracker", "gsf_log_tracker_id", 
                                               string="Log Tracker Lines")
    
    @api.model
    def create(self, vals):
        log_tracker_seq = self.env['ir.sequence'].next_by_code('google.shopping.feed.log.tracker')
        vals.update({'name': log_tracker_seq })
        return super(GoogleShoppingFeedLogTracker, self).create(vals)


class GoogleShoppingFeedLogLineTracker(models.Model):
    _name = 'google.shopping.feed.log.line.tracker'
    _description = "Google Shopping Feed Log Lines Tracker"
    _rec_name = "gsf_log_tracker_id"
    _order = "id desc"

    gsf_log_tracker_id = fields.Many2one("google.shopping.feed.log.tracker", string="Log Tracker")
    operation_type = fields.Selection(related="gsf_log_tracker_id.operation_type", 
        string="Operation Type", store=False, readonly=True)
    message = fields.Text("Log Message")
    record_reference = fields.Char("Reference/ID")
    action_type = fields.Selection([
        ('create', 'Created New'),
        ('delete', 'Delete'),
        ('skip_line', 'Line Skipped'),
        ('terminate_process_with_log', 'Terminate Process With Log')], 'Action Type')
    log_type = fields.Selection([
        ('not_found', 'NOT FOUND'),
        ('mismatch', 'MISMATCH'),
        ('error', 'Error'),
        ('warning', 'Warning'),
        ('success', 'Success')], 'Log Type')
    gsf_log_tracker_id = fields.Many2one("google.shopping.feed.log.tracker", string="Log Tracker")
    update_product_data_queue_line_id = fields.Many2one("update.product.data.queue.line.gcs", 
                                                        string="Log Tracker Line")
    update_product_inventory_info_queue_line_id = fields.Many2one("update.product.inventory.info.queue.line.gcs", 
                                                        string="Log Tracker Line")
    get_product_status_queue_line_id = fields.Many2one("get.product.status.queue.lines.gcs", 
                                                        string="Log Tracker Line")
    import_product_info_queue_line_id = fields.Many2one("import.product.info.queue.line.gcs", 
                                                        string="Log Tracker Line")