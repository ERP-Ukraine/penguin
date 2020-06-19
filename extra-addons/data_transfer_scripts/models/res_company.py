import logging
import functools

from odoo import api, models

_logger = logging.getLogger(__name__)


class ResCompanyTransfer(models.AbstractModel):
    _name = 'res.company.transfer'
    _inherit = 'db.transfer.mixin'
    _description = 'Company Transfer'

    @api.model
    def transfer_data(self):
        tmpl = '%s: %%s' % self._description
        _logger.info(tmpl, 'import begin!')
        sql = '''
            SELECT rcom.id external_id, rcom.partner_id partner_external_id, rcom.name, rpar.street, rpar.street2, 
                   rpar.zip, rpar.website, rcs.code state_code, rpar.phone, rpar.email, rpar.vat, 
                   rcom.company_registry, rpar.city, rcur.name currency_code, rcoun.code country_code
            FROM res_company rcom
                join res_partner rpar on rcom.partner_id = rpar.id
                left join res_currency rcur on rcom.currency_id = rcur.id
                left join res_country rcoun on rpar.country_id = rcoun.id
                left join res_country_state rcs on rpar.state_id = rcs.id;
        '''
        rows = self.fetch(sql)
        RC = self.env['res.company'].sudo()
        company_dict = {c.external_id: c for c in RC.search([])}
        _logger.info(tmpl % 'create or update companies; len="%s"', len(rows))
        for idx, row in enumerate(rows, 1):
            vals = self.get_prepared_vals(row)
            partner_external_id = vals.pop('partner_external_id')
            company = company_dict.get(vals['external_id'])
            _logger.debug(tmpl % 'prepared vals %s', vals)
            if company:
                _logger.debug(tmpl % 'company found; id="%s", external_id="%s"', company.id, company.external_id)
                company.write(vals)
                _logger.debug(tmpl % 'vals written to company; ; id="%s", external_id="%s"',
                              company.id, company.external_id)
            else:
                company = RC.create(vals)
                _logger.debug(tmpl % 'company created; id="%s", external_id="%s"', company.id, company.external_id)
            _logger.info(tmpl % 'processed %s companies', idx)
            company.partner_id.external_id = partner_external_id
            _logger.debug(tmpl % 'external id %s written to company partner' % partner_external_id)

    @api.model
    def get_prepared_vals(self, row):
        vals = super().get_prepared_vals(row)
        utils = self.env['transfer.utils']

        country_code = vals.pop('country_code', False)
        state_code = vals.pop('state_code', False)
        currency_code = vals.pop('currency_code', False)

        if currency_code:
            vals['currency_id'] = utils.get_currency_by_code(currency_code).id
        if country_code:
            vals['country_id'] = utils.get_country_by_code(country_code).id
        if state_code:
            country_id = vals.get('country_id')
            vals['state_id'] = utils.get_state_by_code(state_code, country_id).id

        return vals
