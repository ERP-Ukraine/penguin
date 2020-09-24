from odoo import fields, models


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    penguin_net_price_pc = fields.Monetary(string='Net Price/pc', compute='_compute_penguin_net_price_pc')

    def _compute_penguin_net_price_pc(self):
        for line in self:
            price_info = line.tax_ids.compute_all(
                line.price_unit * (1 - (line.discount or 0.0) / 100.0),
                line.always_set_currency_id,  # use currency_id if it's set or company currency
                1,  # quantity
                product=line.product_id,
                partner=line.move_id.partner_id,
                is_refund=line.move_id.type in ('out_refund', 'in_refund'),
            )
            line.penguin_net_price_pc = price_info['total_excluded']
