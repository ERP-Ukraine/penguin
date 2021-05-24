from odoo import _, fields, models, SUPERUSER_ID


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    external_id = fields.Integer('External ID', copy=False)
    state = fields.Selection(selection_add=[
        ('future_sale', 'Pre-ordered'),
        ('future_sale_confirmation', 'Pre-order confirmed'),
    ])

    def action_send_preorder_confirmation_email(self):
        self.ensure_one()
        if self.env.su:
            # sending mail in sudo was meant for it being sent from superuser
            self = self.with_user(SUPERUSER_ID)
        template_id = self._find_mail_template(force_confirmation_template=True)
        lang = self.env.context.get('lang')
        template = self.env['mail.template'].browse(template_id)
        if template.lang:
            lang = template._render_template(template.lang, 'sale.order', self.ids[0])
        ctx = {
            'default_model': 'sale.order',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'mark_so_as_sent': True,
            # 'custom_layout': "mail.mail_notification_paynow",
            # 'proforma': self.env.context.get('proforma', False),
            'force_email': True,
            'model_description': self.with_context(lang=lang).type_name,
        }
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new',
            'context': ctx,
        }

    def action_preorder(self):
        self.write({'state': 'future_sale',
                    'date_order': fields.Datetime.now()})

    def action_preorder_confirmation(self):
        self.write({'state': 'future_sale_confirmation',
                    'date_order': fields.Datetime.now()})

    def get_confirmation_mail_subject(self):
        if self.state == 'future_sale':
            # Penguin- Auftragseingangsbestätigung
            return _('Penguin – order-entry confirmation – %s') % self.name or ''
        if self.state == 'future_sale_confirmation':
            # Penguin - finale Auftragsbestätigung
            return _('Penguin – final order confirmation – %s') % self.name or ''
        # Dein Penguin Powderwear Einkauf
        return _('Your Penguin Powderwear purchase – %s') % self.name or ''
