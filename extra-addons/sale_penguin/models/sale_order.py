from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    external_id = fields.Integer('External ID', copy=False)
    state = fields.Selection(selection_add=[
        ('future_sale', 'Pre-ordered'),
        ('future_sale_confirmation', 'Order Confirmation')
    ])

    def _find_mail_template(self, force_confirmation_template=False):
        template_id = False

        if self.state == 'future_sale':
            template_id = int(self.env['ir.config_parameter'].sudo().get_param('sale.default_confirmation_template'))
            template_id = self.env['mail.template'].search([('id', '=', template_id)]).id
            if not template_id:
                IMD = self.env['ir.model.data']
                template_id = IMD.xmlid_to_res_id('sale_penguin.mail_template_sale_confirmation', False)
        if not template_id:
            template_id = super()._find_mail_template(force_confirmation_template)

        return template_id

    def _send_confirmation_email(self):
        email_act = self.action_quotation_send()
        email_ctx = email_act.get('context', {})
        self.with_context(**email_ctx).message_post_with_template(email_ctx.get('default_template_id'))

    def action_preorder(self):
        self.write({'state': 'future_sale'})
        self._send_confirmation_email()
