import logging

from odoo import api, models

_logger = logging.getLogger(__name__)


class ResUsersTransfer(models.AbstractModel):
    _name = 'res.users.transfer'
    _inherit = 'db.transfer.mixin'
    _description = 'User Transfer'

    @api.model
    def transfer_data(self):
        tmpl = '%s: %%s' % self._description
        _logger.info(tmpl, 'import begin!')
        # select all active users
        sql = '''
            SELECT rus.id external_id, rus.partner_id partner_external_id, rus.active, rus.login, rpar.name,
                   rus.company_id, rus.share, rus.signature, rus.password_crypt as password,rpar.email, rpar.phone, 
                   rpar.mobile, rpar.website, rpar.street, rpar.street2, rpar.city, rpar.zip, rpar.country_ref, 
                   rpar.customer customer_rank, rpar.supplier supplier_rank, rpar.lang, rpar.company_type, rpar.tz,
                   rcoun.code country_code, rcs.code state_code
            FROM res_users rus
                JOIN res_partner rpar on rus.partner_id = rpar.id
                LEFT JOIN res_country rcoun on rpar.country_id = rcoun.id
                LEFT JOIN res_country_state rcs on rpar.state_id = rcs.id
            WHERE rus.active IS TRUE AND rpar.name NOT LIKE '需要宫作吗%';
        '''
        rows = self.fetch(sql)
        # select portal group id
        sql = '''SELECT rg.id FROM res_groups rg WHERE rg.name = 'Portal';'''
        groups = self.fetch(sql)
        # select all users with portal group
        sql = '''SELECT uid FROM res_groups_users_rel WHERE gid = %s;''' % groups[0]['id']
        portal_users = self.fetch(sql)

        RU = self.env['res.users'].sudo()
        user_dict = {u.external_id: u for u in RU.search([])}
        portal_users_ids = {u['uid'] for u in portal_users}
        _logger.info(tmpl % 'create or update users; len="%s"', len(rows))
        for idx, row in enumerate(rows, 1):
            vals = self.get_prepared_vals(row, portal_users_ids)
            partner_external_id = vals.pop('partner_external_id')
            user = user_dict.get(vals['external_id'])
            _logger.debug(tmpl % 'prepared vals %s', vals)
            if user:
                if user.external_id == self.env.ref('base.user_admin').external_id:
                    _logger.debug(tmpl, 'admin found, remove login and password from vals...')
                    vals.pop('login')
                    vals.pop('password')
                _logger.debug(tmpl % 'user found; id="%s", external_id="%s"', user.id, user.external_id)
                user.write(vals)
                _logger.debug(tmpl % 'vals written to user; id="%s", external_id="%s"', user.id, user.external_id)
            else:
                user = RU.create(vals)
                _logger.debug(tmpl % 'user created; id="%s", external_id="%s"', user.id, user.external_id)
            user.partner_id.external_id = partner_external_id
            _logger.debug(tmpl % 'external id %s written to user partner' % partner_external_id)
            if not idx % 20:
                _logger.info(tmpl % 'processed %s users', idx)

    @api.model
    def get_prepared_vals(self, row, portal_user_ids=None):
        vals = self.env['res.partner.transfer'].get_prepared_vals(row)
        vals['company_ids'] = [(6, 0, [vals['company_id']])]

        if portal_user_ids and vals['external_id'] in portal_user_ids:
            vals['groups_id'] = [(6, 0, [self.env.ref('base.group_portal').id])]

        return vals
