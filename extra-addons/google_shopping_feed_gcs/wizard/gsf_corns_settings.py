#!/usr/bin/python3

from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api

_INTERVAL_TYPES = {
    'minutes': lambda interval: relativedelta(minutes=interval),
    'hours': lambda interval: relativedelta(hours=interval),
    'days': lambda interval: relativedelta(days=interval),
    'weeks': lambda interval: relativedelta(days=7 * interval),
    'months': lambda interval: relativedelta(months=interval),
}

_INTERVAL_TYPES_SELETIONS = [
    ('minutes', 'Minutes'),
    ('hours', 'Hours'),
    ('days', 'Days'),
    ('weeks', 'Weeks'),
    ('months', 'Months')
]


class GSFCronsSettings(models.TransientModel):
    _name = "gsf.crons.settings"
    _description = "Google shopping crons settings"
    
    def _get_gsf_account(self):
        return self._context.get('gsf_account_id', False)
    
    gsf_account_id = fields.Many2one('google.shopping.feed.account',
        string="Google Account",
        default=_get_gsf_account,
        help="Google account's crons"
    )
    
    # Auto Update Products in Google Shopping
    is_auto_update_products_in_gsf = fields.Boolean("Auto Update Products in Google Shopping?", copy=False, default=False)
    auto_update_products_in_gsf_interval_number = fields.Integer(string="Execute Every", help="Repeat every x.")
    auto_update_products_in_gsf_interval_type = fields.Selection(_INTERVAL_TYPES_SELETIONS, string="Interval Unit")
    auto_update_products_in_gsf_nextcall = fields.Datetime(string="Next Execution Date", help="Next planned execution date for this job.")
    auto_update_products_in_gsf_user_id = fields.Many2one("res.users", string="Scheduler User", help="Scheduler User")
    
    # Update product inventory info. to CE
    is_auto_update_products_inventory_info_in_gsf = fields.Boolean("Auto Update Products Inventory Info. in Google Shopping?", copy=False, default=False)
    auto_update_products_inventory_info_in_gsf_interval_number = fields.Integer(string="Execute Every", help="Repeat every x.")
    auto_update_products_inventory_info_in_gsf_interval_type = fields.Selection(_INTERVAL_TYPES_SELETIONS, string="Interval Unit")
    auto_update_products_inventory_info_in_gsf_nextcall = fields.Datetime(string="Next Execution Date", help="Next planned execution date for this job.")
    auto_update_products_inventory_info_in_gsf_user_id = fields.Many2one("res.users", string="Scheduler User", help="Scheduler User")
        
    # Auto Get Products Status from Google Shopping
    is_auto_get_products_status_from_gsf = fields.Boolean("Auto Get Products Status from Google Shopping?", copy=False, default=False)    
    auto_get_products_status_from_gsf_interval_number = fields.Integer(string="Execute Every", help="Repeat every x.")
    auto_get_products_status_from_gsf_interval_type = fields.Selection(_INTERVAL_TYPES_SELETIONS, string="Interval Unit")
    auto_get_products_status_from_gsf_nextcall = fields.Datetime(string="Next Execution Date", help="Next planned execution date for this job.")
    auto_get_products_status_from_gsf_user_id = fields.Many2one("res.users", string="Scheduler User", help="Scheduler User")
    
    # Auto Import Products Information from Google Shopping
    is_auto_import_products_info_from_gsf = fields.Boolean("Auto Import Product Info. from Google Shopping?", copy=False, default=False)    
    auto_import_products_info_from_gsf_interval_number = fields.Integer(string="Execute Every", help="Repeat every x.")
    auto_import_products_info_from_gsf_interval_type = fields.Selection(_INTERVAL_TYPES_SELETIONS, string="Interval Unit")
    auto_import_products_info_from_gsf_nextcall = fields.Datetime(string="Next Execution Date", help="Next planned execution date for this job.")
    auto_import_products_info_from_gsf_user_id = fields.Many2one("res.users", string="Scheduler User", help="Scheduler User")
    
    
    @api.onchange("gsf_account_id")
    def onchange_gsf_account_id(self):
        gsf_account_id = self.gsf_account_id
        self.auto_update_products_in_gsf_values(gsf_account_id)
        self.auto_update_products_inventory_info_in_gsf_values(gsf_account_id)
        self.auto_get_products_status_from_gsf_values(gsf_account_id)
        self.auto_import_products_info_from_gsf_values(gsf_account_id)
        
    def auto_update_products_in_gsf_values(self, gsf_account_id):
        try:
            cron_id = gsf_account_id and self.env.ref(
                'google_shopping_feed_gcs.ir_cron_auto_update_products_in_gsf_%d' % gsf_account_id.id)
        except:
            cron_id = False
        if cron_id:
            self.is_auto_update_products_in_gsf = cron_id.active or False
            self.auto_update_products_in_gsf_interval_number = cron_id.interval_number or False
            self.auto_update_products_in_gsf_interval_type = cron_id.interval_type or False
            self.auto_update_products_in_gsf_nextcall = cron_id.nextcall or False
            self.auto_update_products_in_gsf_user_id = cron_id.user_id.id or False
            
    def auto_update_products_inventory_info_in_gsf_values(self, gsf_account_id):
        try:
            cron_id = gsf_account_id and self.env.ref(
                'google_shopping_feed_gcs.ir_cron_auto_update_products_inventory_info_in_gsf_%d' % gsf_account_id.id)
        except:
            cron_id = False
        if cron_id:
            self.is_auto_update_products_inventory_info_in_gsf = cron_id.active or False
            self.auto_update_products_inventory_info_in_gsf_interval_number = cron_id.interval_number or False
            self.auto_update_products_inventory_info_in_gsf_interval_type = cron_id.interval_type or False
            self.auto_update_products_inventory_info_in_gsf_nextcall = cron_id.nextcall or False
            self.auto_update_products_inventory_info_in_gsf_user_id = cron_id.user_id.id or False
            
    def auto_get_products_status_from_gsf_values(self, gsf_account_id):
        try:
            cron_id = gsf_account_id and self.env.ref(
                'google_shopping_feed_gcs.ir_cron_auto_get_products_status_from_gsf_%d' % gsf_account_id.id)
        except:
            cron_id = False
        if cron_id:
            self.is_auto_get_products_status_from_gsf = cron_id.active or False
            self.auto_get_products_status_from_gsf_interval_number = cron_id.interval_number or False
            self.auto_get_products_status_from_gsf_interval_type = cron_id.interval_type or False
            self.auto_get_products_status_from_gsf_nextcall = cron_id.nextcall or False
            self.auto_get_products_status_from_gsf_user_id = cron_id.user_id.id or False
    
    def auto_import_products_info_from_gsf_values(self, gsf_account_id):
        try:
            cron_id = gsf_account_id and self.env.ref(
                'google_shopping_feed_gcs.ir_cron_auto_import_products_info_from_gsf_%d' % gsf_account_id.id)
        except:
            cron_id = False
        if cron_id:
            print(cron_id)
            self.is_auto_import_products_info_from_gsf = cron_id.active or False
            self.auto_import_products_info_from_gsf_interval_number = cron_id.interval_number or False
            self.auto_import_products_info_from_gsf_interval_type = cron_id.interval_type or False
            self.auto_import_products_info_from_gsf_nextcall = cron_id.nextcall or False
            self.auto_import_products_info_from_gsf_user_id = cron_id.user_id.id or False
    
    def action_save_gsf_crons_setting(self):
        gsf_account_id = self.gsf_account_id
        self.auto_update_products_in_gsf_cron_configuration(gsf_account_id)
        self.auto_update_products_inventory_info_in_gsf_cron_configuration(gsf_account_id)
        self.auto_get_products_status_from_gsf_cron_configuration(gsf_account_id)
        self.auto_import_products_info_from_gsf_cron_configuration(gsf_account_id)
        vals = {
            'is_auto_update_products_in_gsf': self.is_auto_update_products_in_gsf,
            'is_auto_update_products_inventory_info_in_gsf': self.is_auto_update_products_inventory_info_in_gsf,
            'is_auto_get_products_status_from_gsf': self.is_auto_get_products_status_from_gsf,
            'is_auto_import_products_info_from_gsf': self.is_auto_import_products_info_from_gsf,
        }
        gsf_account_id.write(vals)
        return True
    
    def auto_update_products_in_gsf_cron_configuration(self, gsf_account_id):
        if self.is_auto_update_products_in_gsf:
            try:
                cron_id = self.env.ref(
                    'google_shopping_feed_gcs.ir_cron_auto_update_products_in_gsf_%d' % gsf_account_id.id,
                    raise_if_not_found=False
                )
            except:
                cron_id = False
                
            nextcall = datetime.now()
            auto_update_products_in_gsf_interval_type = self.auto_update_products_in_gsf_interval_type
            auto_update_products_in_gsf_interval_number = self.auto_update_products_in_gsf_interval_number
            nextcall += _INTERVAL_TYPES[auto_update_products_in_gsf_interval_type](auto_update_products_in_gsf_interval_number)
            vals = {
                'active': True,
                'interval_number': auto_update_products_in_gsf_interval_number,
                'interval_type': auto_update_products_in_gsf_interval_type,
                'nextcall': nextcall.strftime('%Y-%m-%d %H:%M:%S'),
                'user_id': self.auto_update_products_in_gsf_user_id and self.auto_update_products_in_gsf_user_id.id,
                'code': "model.auto_update_products_in_gsf_cron({'gsf_account_id':%d})" % gsf_account_id.id,
                'gsf_account_id': gsf_account_id.id
            }
            if cron_id:
                vals.update({'name': cron_id.name})
                cron_id.write(vals)
            else:
                try:
                    auto_updates_products_in_gsf_cron = self.env.ref('google_shopping_feed_gcs.ir_cron_auto_update_products_in_gsf')
                except:
                    auto_updates_products_in_gsf_cron = False
                    
                if not auto_updates_products_in_gsf_cron:
                    raise Warning(
                        'Core settings of Google Shopping are deleted,'
                        ' please upgrade Odoo Google Shopping Connector module to back this settings.'
                    )
                name = gsf_account_id.name + ' : ' + auto_updates_products_in_gsf_cron.name
                vals.update({'name': name})
                new_cron = auto_updates_products_in_gsf_cron.copy(default=vals)
                self.env['ir.model.data'].create({
                    'module': 'google_shopping_feed_gcs',
                    'name': 'ir_cron_auto_update_products_in_gsf_%d' % gsf_account_id.id,
                    'model': 'ir.cron',
                    'res_id': new_cron.id,
                    'noupdate': True
                })
        else:
            try:
                cron_id = self.env.ref('google_shopping_feed_gcs.ir_cron_auto_update_products_in_gsf_%d' % gsf_account_id.id)
            except:
                cron_id = False
            cron_id and cron_id.write({'active': False})
        return True
    
    def auto_update_products_inventory_info_in_gsf_cron_configuration(self, gsf_account_id):
        if self.is_auto_update_products_inventory_info_in_gsf:
            try:
                cron_id = self.env.ref(
                    'google_shopping_feed_gcs.ir_cron_auto_update_products_inventory_info_in_gsf_%d' % gsf_account_id.id,
                    raise_if_not_found=False
                )
            except:
                cron_id = False
                
            nextcall = datetime.now()
            auto_update_products_inventory_info_in_gsf_interval_type = self.auto_update_products_inventory_info_in_gsf_interval_type
            auto_update_products_inventory_info_in_gsf_interval_number = self.auto_update_products_inventory_info_in_gsf_interval_number
            nextcall += _INTERVAL_TYPES[auto_update_products_inventory_info_in_gsf_interval_type](auto_update_products_inventory_info_in_gsf_interval_number)
            vals = {
                'active': True,
                'interval_number': auto_update_products_inventory_info_in_gsf_interval_number,
                'interval_type': auto_update_products_inventory_info_in_gsf_interval_type,
                'nextcall': nextcall.strftime('%Y-%m-%d %H:%M:%S'),
                'user_id': self.auto_update_products_inventory_info_in_gsf_user_id and self.auto_update_products_inventory_info_in_gsf_user_id.id,
                'code': "model.auto_update_products_inventory_info_in_gsf_cron({'gsf_account_id':%d})" % gsf_account_id.id,
                'gsf_account_id': gsf_account_id.id
            }
            if cron_id:
                vals.update({'name': cron_id.name})
                cron_id.write(vals)
            else:
                try:
                    auto_update_products_inventory_info_in_gsf_cron = self.env.ref('google_shopping_feed_gcs.ir_cron_auto_update_products_inventory_info_in_gsf')
                except:
                    auto_update_products_inventory_info_in_gsf_cron = False
                    
                if not auto_update_products_inventory_info_in_gsf_cron:
                    raise Warning(
                        'Core settings of Google Shopping are deleted,'
                        ' please upgrade Odoo Google Shopping Connector module to back this settings.'
                    )
                name = gsf_account_id.name + ' : ' + auto_update_products_inventory_info_in_gsf_cron.name
                vals.update({'name': name})
                new_cron = auto_update_products_inventory_info_in_gsf_cron.copy(default=vals)
                self.env['ir.model.data'].create({
                    'module': 'google_shopping_feed_gcs',
                    'name': 'ir_cron_auto_update_products_inventory_info_in_gsf_%d' % gsf_account_id.id,
                    'model': 'ir.cron',
                    'res_id': new_cron.id,
                    'noupdate': True
                })
        else:
            try:
                cron_id = self.env.ref('google_shopping_feed_gcs.ir_cron_auto_update_products_inventory_info_in_gsf_%d' % gsf_account_id.id)
            except:
                cron_id = False
            cron_id and cron_id.write({'active': False})
        return True
    
    def auto_get_products_status_from_gsf_cron_configuration(self, gsf_account_id):
        if self.is_auto_get_products_status_from_gsf:
            try:
                cron_id = self.env.ref(
                    'google_shopping_feed_gcs.ir_cron_auto_get_products_status_from_gsf_%d' % gsf_account_id.id,
                    raise_if_not_found=False
                )
            except:
                cron_id = False
                
            nextcall = datetime.now()
            auto_get_products_status_from_gsf_interval_type = self.auto_get_products_status_from_gsf_interval_type
            auto_get_products_status_from_gsf_interval_number = self.auto_get_products_status_from_gsf_interval_number
            nextcall += _INTERVAL_TYPES[auto_get_products_status_from_gsf_interval_type](auto_get_products_status_from_gsf_interval_number)
            vals = {
                'active': True,
                'interval_number': auto_get_products_status_from_gsf_interval_number,
                'interval_type': auto_get_products_status_from_gsf_interval_type,
                'nextcall': nextcall.strftime('%Y-%m-%d %H:%M:%S'),
                'user_id': self.auto_get_products_status_from_gsf_user_id and self.auto_get_products_status_from_gsf_user_id.id,
                'code': "model.auto_get_products_status_from_gsf_cron({'gsf_account_id':%d})" % gsf_account_id.id,
                'gsf_account_id': gsf_account_id.id
            }
            if cron_id:
                vals.update({'name': cron_id.name})
                cron_id.write(vals)
            else:
                try:
                    auto_get_products_status_from_gsf_cron = self.env.ref('google_shopping_feed_gcs.ir_cron_auto_get_products_status_from_gsf')
                except:
                    auto_get_products_status_from_gsf_cron = False
                    
                if not auto_get_products_status_from_gsf_cron:
                    raise Warning(
                        'Core settings of Google Shopping are deleted,'
                        ' please upgrade Odoo Google Shopping Connector module to back this settings.'
                    )
                name = gsf_account_id.name + ' : ' + auto_get_products_status_from_gsf_cron.name
                vals.update({'name': name})
                new_cron = auto_get_products_status_from_gsf_cron.copy(default=vals)
                self.env['ir.model.data'].create({
                    'module': 'google_shopping_feed_gcs',
                    'name': 'ir_cron_auto_get_products_status_from_gsf_%d' % gsf_account_id.id,
                    'model': 'ir.cron',
                    'res_id': new_cron.id,
                    'noupdate': True
                })
        else:
            try:
                cron_id = self.env.ref('google_shopping_feed_gcs.ir_cron_auto_get_products_status_from_gsf_%d' % gsf_account_id.id)
            except:
                cron_id = False
            cron_id and cron_id.write({'active': False})
        return True
    
    def auto_import_products_info_from_gsf_cron_configuration(self, gsf_account_id):
        if self.is_auto_import_products_info_from_gsf:
            try:
                cron_id = self.env.ref(
                    'google_shopping_feed_gcs.ir_cron_auto_import_products_info_from_gsf_%d' % gsf_account_id.id,
                    raise_if_not_found=False
                )
            except:
                cron_id = False
                
            nextcall = datetime.now()
            auto_import_products_info_from_gsf_interval_type = self.auto_import_products_info_from_gsf_interval_type
            auto_import_products_info_from_gsf_interval_number = self.auto_import_products_info_from_gsf_interval_number
            nextcall += _INTERVAL_TYPES[auto_import_products_info_from_gsf_interval_type](auto_import_products_info_from_gsf_interval_number)
            vals = {
                'active': True,
                'interval_number': auto_import_products_info_from_gsf_interval_number,
                'interval_type': auto_import_products_info_from_gsf_interval_type,
                'nextcall': nextcall.strftime('%Y-%m-%d %H:%M:%S'),
                'user_id': self.auto_import_products_info_from_gsf_user_id and self.auto_import_products_info_from_gsf_user_id.id,
                'code': "model.auto_import_products_info_from_gsf_cron({'gsf_account_id':%d})" % gsf_account_id.id,
                'gsf_account_id': gsf_account_id.id
            }
            if cron_id:
                vals.update({'name': cron_id.name})
                cron_id.write(vals)
            else:
                try:
                    auto_import_products_info_from_gsf_cron = self.env.ref('google_shopping_feed_gcs.ir_cron_auto_import_products_info_from_gsf')
                except:
                    auto_import_products_info_from_gsf_cron = False
                    
                if not auto_import_products_info_from_gsf_cron:
                    raise Warning(
                        'Core settings of Google Shopping are deleted,'
                        ' please upgrade Odoo Google Shopping Connector module to back this settings.'
                    )
                name = gsf_account_id.name + ' : ' + auto_import_products_info_from_gsf_cron.name
                vals.update({'name': name})
                new_cron = auto_import_products_info_from_gsf_cron.copy(default=vals)
                self.env['ir.model.data'].create({
                    'module': 'google_shopping_feed_gcs',
                    'name': 'ir_cron_auto_import_products_info_from_gsf_%d' % gsf_account_id.id,
                    'model': 'ir.cron',
                    'res_id': new_cron.id,
                    'noupdate': True
                })
        else:
            try:
                cron_id = self.env.ref('google_shopping_feed_gcs.ir_cron_auto_import_products_info_from_gsf_%d' % gsf_account_id.id)
            except:
                cron_id = False
            cron_id and cron_id.write({'active': False})
        return True
    
    
    
    
    
    
    
    
    
    
