# -*- coding: utf-8 -*-
#!/usr/bin/python3
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import models, fields, api, _

class GoogleShoppingQueueProcessWizardGcs(models.TransientModel):
    _name = 'google.shopping.queue.process.wizard.gcs'
    _description = "Google Shopping Queue Process Wizard GCS"
    
    def move_to_completed_queue(self):
        queue_process_action = self._context.get('queue_process_action') or ""
        if queue_process_action == "move_to_completed_product_queue":
            self.move_to_completed_product_queue_manually()
        elif queue_process_action == "move_to_completed_product_inventory_info_queue":
            self.move_to_completed_product_inventory_info_queue_manually()
        elif queue_process_action == "move_to_completed_get_product_status_queue":
            self.move_to_completed_get_product_status_queue_manually()
        elif queue_process_action == "move_to_completed_import_product_info_queue":
            self.move_to_completed_import_product_info_queue_manually()
        return True

    def move_to_completed_product_queue_manually(self):
        update_product_data_queue_gcs_obj = self.env["update.product.data.queue.gcs"]
        queue_active_ids = self._context.get('active_ids')
        update_product_data_queue_ids = update_product_data_queue_gcs_obj.browse(queue_active_ids)
        for update_product_data_queue_id in update_product_data_queue_ids:
            queue_lines = update_product_data_queue_id.update_product_data_queue_lines.filtered(
                lambda line: line.state in ['draft', 'failed'])
            queue_lines.write({'state': 'cancel'})
            update_product_data_queue_id.message_post(
                body=_("Manually moved to cancel queues are %s.") % (queue_lines.mapped('product_offer_id')))
        return True
    
    def move_to_completed_product_inventory_info_queue_manually(self):
        queue_obj = self.env["update.product.inventory.info.queue.gcs"]
        queue_active_ids = self._context.get('active_ids')
        queue_ids = queue_obj.browse(queue_active_ids)
        for queue_id in queue_ids:
            queue_lines = queue_id.update_product_inventory_info_queue_lines.filtered(
                lambda line: line.state in ['draft', 'failed'])
            queue_lines.write({'state': 'cancel'})
            queue_id.message_post(
                body=_("Manually moved to cancel queues are %s.") % (queue_lines.mapped('product_offer_id')))
        return True
    
    def move_to_completed_get_product_status_queue_manually(self):
        queue_obj = self.env["get.product.status.queue.gcs"]
        queue_active_ids = self._context.get('active_ids')
        queue_ids = queue_obj.browse(queue_active_ids)
        for queue_id in queue_ids:
            queue_lines = queue_id.get_product_status_queue_lines.filtered(
                lambda line: line.state in ['draft', 'failed'])
            queue_lines.write({'state': 'cancel'})
            queue_id.message_post(
                body=_("Manually moved to cancel queues are %s.") % (queue_lines.mapped('product_offer_id')))
        return True
    
    def move_to_completed_import_product_info_queue_manually(self):
        queue_obj = self.env["import.product.info.queue.gcs"]
        queue_active_ids = self._context.get('active_ids')
        queue_ids = queue_obj.browse(queue_active_ids)
        for queue_id in queue_ids:
            queue_lines = queue_id.import_product_info_queue_lines.filtered(
                lambda line: line.state in ['draft', 'failed'])
            queue_lines.write({'state': 'cancel'})
            queue_id.message_post(
                body=_("Manually moved to cancel queues are %s.") % (queue_lines.mapped('product_offer_id')))
        return True