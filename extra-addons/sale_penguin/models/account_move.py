from odoo import api, models


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    @api.depends('sale_line_ids.penguin_rrp_pc', 'sale_line_ids.penguin_net_price_pc')
    def _compute_penguin_rrp(self):
        for line in self:
            sale_line = line.sale_line_ids[:1]
            if not sale_line:
                line.penguin_rrp_pc = 0
                line.penguin_net_price_pc = 0
            line.penguin_rrp_pc = sale_line.penguin_rrp_pc
            line.penguin_net_price_pc = sale_line.penguin_net_price_pc
