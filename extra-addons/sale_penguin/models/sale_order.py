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
        self.order_line._validate_analytic_distribution()
        lang = self.env.context.get('lang')
        mail_template = self._find_mail_template()
        if mail_template and mail_template.lang:
            lang = mail_template._render_lang(self.ids)[self.id]
        ctx = {
            'default_model': 'sale.order',
            'default_res_ids': self.ids,
            'default_template_id': mail_template.id if mail_template else None,
            'default_composition_mode': 'comment',
            'mark_so_as_sent': True,
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

    def _confirmation_error_message(self):
        self.ensure_one()
        if self.state in {'future_sale_confirmation'}:
            return False
        return super()._confirmation_error_message()

    def _find_mail_template(self):
        self.ensure_one()
        if self.env.context.get('proforma') or self.state not in ['sale', 'future_sale', 'future_sale_confirmation']:
            return self.env.ref('sale.email_template_edi_sale', raise_if_not_found=False)
        else:
            return self._get_confirmation_template()

    def _get_confirmation_template(self):
        self.ensure_one()
        if  self.state in ['sale', 'future_sale', 'future_sale_confirmation'] and not self.env.context.get('proforma', False):
            peng_mail = self.env.ref('sale_penguin.mail_template_sale_confirmation', raise_if_not_found=False)
            if peng_mail:
                return peng_mail
        return super()._get_confirmation_template()
