from odoo import fields, models


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    penguin_rrp_pc = fields.Monetary(string='RRP/pc', compute='_compute_penguin_rrp')
    penguin_net_price_pc = fields.Monetary(string='Net Price/pc', compute='_compute_penguin_rrp')

    def _compute_penguin_rrp(self):
        for line in self:
            line.penguin_rrp_pc = 0
            line.penguin_net_price_pc = 0
