from odoo import fields, models, api


class Partner(models.Model):
    _inherit = 'res.partner'

    ffn_id = fields.Char(string='FFN User ID')
    ffn_is_active = fields.Boolean(string='FFN Active')

    def authorize_ffn_product(self):
        return {
            'name': 'Grant a fulfiller access to all product',
            'type': 'ir.actions.act_window',
            'res_model': 'ffn.authorize',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_partner_id': self.id,
                'default_show_grant_all': True,
            }
        }
