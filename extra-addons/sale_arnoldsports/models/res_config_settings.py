from odoo import _, api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    arnold_alias_prefix = fields.Char('Alias for ArnoldSports Orders')
    generate_arnold_orders = fields.Boolean(
        'Generate ArnoldSports Orders',
        config_parameter='sale_arnoldsports.generate_arnold_orders')
    arnold_partner_id = fields.Many2one(
        'res.partner',
        string='Customer for Sales Orders',
        config_parameter='sale_arnoldsports.arnold_partner_id')

    def _find_default_lead_alias_id(self):
        alias = self.env.ref('sale_arnoldsports.mail_alias_arnold', False)
        if not alias:
            alias = self.env['mail.alias'].search([
                ('alias_model_id.model', '=', 'sale.order.arnold.report'),
                ('alias_parent_model_id.model', '=', 'sale.order'),
            ], limit=1)
        return alias

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        alias = self._find_default_lead_alias_id()
        res.update(
            arnold_alias_prefix=alias.alias_name if alias else False,
        )
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        alias = self._find_default_lead_alias_id()
        if alias:
            alias.write({'alias_name': self.arnold_alias_prefix})
        else:
            self.env['mail.alias'].create({
                'alias_name': self.arnold_alias_prefix,
                'alias_model_id': self.env['ir.model']._get('sale.order.arnold.report').id,
                'alias_parent_model_id': self.env['ir.model']._get('sale.order').id,
            })
