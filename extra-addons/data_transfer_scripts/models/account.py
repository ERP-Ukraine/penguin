import logging

from odoo import api, models

_logger = logging.getLogger(__name__)


class ProductProductTransfer(models.AbstractModel):
    _name = 'account.fiscal.position.transfer'
    _inherit = 'db.transfer.mixin'
    _description = 'Account Fiscal Position'

    @api.model
    def transfer_data(self):
        tmpl = '%s: %%s' % self._description
        _logger.info(tmpl, 'import begin!')
        
        AFP = self.env['account.fiscal.position'].sudo()
        fiscal_list = ((1, 'Import/Export'), (4, 'Geschäftspartner EU (mit USt-ID)'),
                       (5, 'Geschäftspartner Ausland (Nicht-EU)'), (6, 'Geschäftspartner EU (mit USt-ID)'),
                       (7, 'Geschäftspartner EU (ohne USt-ID)'))
        fiscal_dict = {f[0]: AFP.search([('name', '=', f[1])], limit=1).id for f in fiscal_list}

        # select all partner with fiscal position
        sql = '''
            SELECT  split_part(value_reference, ',', 2)::INTEGER fiscal_position_id, 
                    split_part(res_id, ',', 2)::INTEGER res_id
            FROM ir_property
            WHERE name = 'property_account_position_id';
        '''
        rows = self.fetch(sql)
        RP = self.env['res.partner'].sudo()
        partner_ids = RP.search([('external_id', 'in', [r['res_id'] for r in rows])])
        partner_dict = {p.external_id: p for p in partner_ids}
        _logger.info(tmpl % 'add fiscal position to customers; len="%s"', len(rows))
        for idx, row in enumerate(rows, 1):
            vals = self.get_prepared_vals(row)
            fiscal_position_id = fiscal_dict.get(vals['fiscal_position_id'])
            partner = partner_dict.get(vals['res_id'])
            if partner:
                partner.property_account_position_id = fiscal_position_id
            if not idx % 30:
                _logger.info(tmpl % 'processed %s customers (partners)', idx)
