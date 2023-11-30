#!/usr/bin/python3
from odoo import models, fields


class IrCron(models.Model):
    _inherit = 'ir.cron'

    gsf_account_id = fields.Many2one('google.shopping.feed.account',
        string="Google Account",
        help="Google account's crons"
    )
