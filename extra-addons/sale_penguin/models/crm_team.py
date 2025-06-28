from odoo import fields, models


class CrmTeam(models.Model):
    _inherit = 'crm.team'

    # override domain
    member_ids = fields.One2many(
        'res.users', 'sale_team_id', string='Channel Members', check_company=True,
        domain=lambda self: [('is_salesperson', '=', True)],
        help="Add members to automatically assign their documents to this sales team. You can only be member of one team.")
