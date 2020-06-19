import logging

from odoo import api, models

from collections import defaultdict

_logger = logging.getLogger(__name__)


class ResPartnerTransfer(models.AbstractModel):
    _name = 'res.partner.transfer'
    _inherit = 'db.transfer.mixin'
    _description = 'Customer Transfer'

    @api.model
    def transfer_data(self):
        tmpl = '%s: %%s' % self._description
        _logger.info(tmpl, 'import begin!')
        # select all active users
        sql = '''
            SELECT rpar.id external_id, rpar.parent_id parent_id, rpar.name, rpar.email, rpar.phone, rpar.mobile, 
                   rpar.website, rpar.street, rpar.street2, rpar.city, rpar.zip, rpar.country_ref, 
                   rpar.customer customer_rank, rpar.supplier supplier_rank, rpar.lang, rpar.tz,
                   rpar.company_type, rpar.parent_id, rpar.comment, rpar.ref, rpar.type, rcoun.code country_code,
                   rpar.company_id, rcs.code state_code
            FROM res_partner rpar
                LEFT JOIN res_country rcoun on rpar.country_id = rcoun.id
                LEFT JOIN res_country_state rcs on rpar.state_id = rcs.id
            WHERE rpar.active IS TRUE AND rpar.name NOT LIKE '需要宫作吗%';
        '''
        rows = self.fetch(sql)
        RP = self.env['res.partner'].sudo()
        partner_ids = RP.search([])
        partner_dict = {p.external_id: p for p in partner_ids}
        parent_dict = {}
        _logger.info(tmpl % 'create or update customers (partners); len="%s"', len(rows))
        for idx, row in enumerate(rows, 1):
            vals = self.get_prepared_vals(row)
            parent_external_id = vals.pop('parent_id')
            partner = partner_dict.get(vals['external_id'])
            _logger.debug(tmpl % 'prepared vals %s', vals)
            if partner:
                _logger.debug(tmpl % 'partner found; id="%s", external_id="%s"', partner.id, partner.external_id)
                if partner.user_ids:
                    user = partner.user_ids[0]
                    _logger.debug(tmpl % 'company moved from user, user_id="%s" company_id=%s',
                                  user.id, user.company_id.id)
                    vals['company_id'] = partner.user_ids[0].company_id.id
                partner.write(vals)
                _logger.debug(tmpl % 'vals written to partner; id="%s", external_id="%s"',
                              partner.id, partner.external_id)
            else:
                partner = RP.create(vals)
                _logger.debug(tmpl % 'partner created; id="%s", external_id="%s"', partner.id, partner.external_id)
            if parent_external_id:
                _logger.debug(tmpl % 'partner with id="%s" has parent with external_id="%s"',
                              partner.id, parent_external_id)
                parent_dict[partner] = parent_external_id
                _logger.debug(tmpl % 'parent added to parent dict')
            if not idx % 200:
                _logger.info(tmpl % 'processed %s customers (partners)', idx)

        if parent_dict:
            utils = self.env['transfer.utils']
            _logger.info(tmpl % 'create or update customer (partners) parent; len="%s"', len(parent_dict.keys()))
            idx = 0
            for partner, partner_external_id in parent_dict.items():
                parent_id = utils.browse_ext_id('res.partner', partner_external_id).id
                partner.parent_id = parent_id
                _logger.debug(tmpl % 'parent with id="%s" written to partner with id="%s"', parent_id, partner.id)
                idx += 1
                if not idx % 10:
                    _logger.info(tmpl % 'processed %s customer (partner) parents', idx)

    @api.model
    def get_prepared_vals(self, row):
        vals = super().get_prepared_vals(row)

        RL = self.env['res.lang']
        if vals['lang'] and not RL._lang_get_id(vals['lang']):
            RL.load_lang(vals['lang'])

        vals['customer_rank'] = int(vals['customer_rank'] or False)
        vals['supplier_rank'] = int(vals['supplier_rank'] or False)

        utils = self.env['transfer.utils']
        country_code = vals.pop('country_code', False)
        state_code = vals.pop('state_code', False)
        if country_code:
            vals['country_id'] = utils.get_country_by_code(country_code).id
        if state_code:
            country_id = vals.get('country_id')
            vals['state_id'] = utils.get_state_by_code(state_code, country_id).id
        vals['company_id'] = utils.browse_ext_id('res.company', vals['company_id']).id

        return vals
