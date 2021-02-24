from odoo import _, fields, models, SUPERUSER_ID


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    external_id = fields.Integer('External ID', copy=False)
    state = fields.Selection(selection_add=[
        ('future_sale', 'Pre-ordered'),
        ('future_sale_confirmation', 'Pre-order confirmed'),
    ])

    def action_send_preorder_confirmation_email(self):
        if self.env.su:
            # sending mail in sudo was meant for it being sent from superuser
            self = self.with_user(SUPERUSER_ID)
        template_id = self._find_mail_template(force_confirmation_template=True)
        if template_id:
            for order in self:
                order.with_context(
                    force_send=True).message_post_with_template(
                        template_id, composition_mode='comment')

    def action_preorder(self):
        self.write({'state': 'future_sale'})

    def action_preorder_confirmation(self):
        self.write({'state': 'future_sale_confirmation'})

    def get_confirmation_mail_subject(self):
        if self.state == 'future_sale':
            # Penguin- Auftragseingangsbestätigung
            return _('Penguin – order-entry confirmation – %s') % self.name or ''
        if self.state == 'future_sale_confirmation':
            # Penguin - finale Auftragsbestätigung
            return _('Penguin – final order confirmation – %s') % self.name or ''
        # Dein Penguin Powderwear Einkauf
        return _('Your Penguin Powderwear purchase – %s') % self.name or ''
