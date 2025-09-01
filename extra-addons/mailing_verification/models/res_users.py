import logging
from odoo import _, api, models

_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.model
    def _signup_create_user(self, values):
        if 'partner_id' not in values:
            self = self.with_context(not_verified=True)
        return super()._signup_create_user(values)

    @api.model_create_multi
    def create(self, vals_list):
        users = super().create(vals_list)
        if self.env.context.get('not_verified'):
            for user in users:
                user.partner_id.is_verified = False
                user.partner_id.mailing_contact_ids.is_verified = False
                contact_verification = self.env['contact.verification'].sudo().create({'partner_id': user.partner_id.id})
                try:
                    template_id = self.env.ref('mailing_verification.mail_verification_email')
                    template_id.sudo().send_mail(contact_verification.id, force_send=True)
                except Exception as e:
                    _logger.info(_("Error! Email cannot be send %s", str(e)))
        return users
