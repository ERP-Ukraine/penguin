import logging
import psycopg2

from odoo import _, api, models, tools
from odoo.exceptions import UserError

from psycopg2.extras import DictCursor

_logger = logging.getLogger(__name__)


class DBDataTransfer(models.AbstractModel):
    _name = 'db.data.transfer'
    _description = 'DB Data Transfer'

    @api.model
    def transfer_models_data(self, model_list):
        set_param = self.env['ir.config_parameter'].sudo().set_param
        get_param = self.env['ir.config_parameter'].sudo().get_param
        tmpl = 'Transfer model data: %s'
        error_messages = []
        for model in model_list:
            _logger.info(tmpl % 'import data from "%s" model...', model)
            if get_param('%s.data.transferred' % model):
                _logger.info(tmpl % 'data from model "%s" already transferred', model)
                continue
            try:
                self.env['%s.transfer' % model].with_context(tracking_disable=True).sudo().transfer_data()
                set_param('%s.data.transferred' % model, True)
                _logger.info(tmpl % 'data transfer from "%s" model successfully completed!', model)
                self.env.cr.commit()
                _logger.info(tmpl % 'changes committed')
            except Exception as e:
                error_msg = tmpl % 'model="%s", error="%s"' % (model, e)
                _logger.error(error_msg, exc_info=True)
                error_messages.append(error_msg)
        if error_messages:
            raise UserError('\n'.join(error_messages))


class DBTransferMixin(models.AbstractModel):
    _name = 'db.transfer.mixin'
    _description = 'DB Transfer Mixin'

    @api.model
    def _get_db_params(self, params=None):
        if params is None:
            params = {}
        get_param = self.env['ir.config_parameter'].sudo().get_param
        return {
            'dbname': get_param('database.old.dbname'),
            'user': get_param('database.old.user'),
            'password': get_param('database.old.password'),
            'host': get_param('database.old.host'),
            'port': get_param('database.old.port'),
            **params
        }

    @api.model
    def fetch(self, sql, dsn=None):
        db_params = self._get_db_params(dsn)
        with psycopg2.connect(cursor_factory=DictCursor, **db_params) as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                result = cursor.fetchall()
        return result

    @api.model
    def get_prepared_vals(self, row):
        """Method to override. Return prepared row dict

        :param row: sql RowDict object
        :return: python dict object
        """
        if not isinstance(row, dict):
            return dict(row)
        return row.copy()


class DBCatalogMixin(models.AbstractModel):
    _name = 'db.transfer.catalog.mixin'
    _inherit = 'db.transfer.mixin'
    _description = 'DB Transfer Catalog Mixin'

    @api.model
    def _transfer_data(self, sql, model, log_prefix='Transfer Data'):
        tmpl = '%s: %%s' % log_prefix
        _logger.info(tmpl, 'import begin!')
        Model = self.env[model].sudo()
        record_ids = Model.search([])
        record_dict = {i.external_id: i for i in record_ids}
        rows = self.fetch(sql)
        _logger.debug('create or update records, len="%s"', len(rows))
        for idx, row in enumerate(rows):
            vals = self.get_prepared_vals(row)
            rec = record_dict.get(vals['external_id'])
            _logger.debug(tmpl % 'prepared vals %s', vals)
            if rec:
                _logger.debug(tmpl % 'found record with external id %s', rec.external_id)
                rec.write(vals)
                _logger.debug(tmpl % 'vals written; id="%s", external_id="%s"', rec.id, rec.external_id)
            else:
                rec = Model.create(vals)
                record_dict[rec.external_id] = rec
                _logger.debug(tmpl % 'record created; id="%s", external_id="%s"', rec.id, rec.external_id)
            if not idx % 10:
                _logger.info(tmpl % 'processed %s records', idx)


class TransferUtils(models.AbstractModel):
    _name = 'transfer.utils'
    _description = 'Transfer Utils'

    @api.model
    @tools.ormcache('code')
    def get_currency_by_code(self, code=None):
        """Returns currency record by currency ISO code."""
        if not code:
            raise UserError(_("Empty currency code"))
        RS = self.env['res.currency'].with_context(active_test=False)
        currency = RS.search([('name', '=', code)], limit=1)
        if not currency:
            raise UserError(_("Unknown currency code %s") % code)
        if not currency.active:
            currency.active = True
            if hasattr(self.env.user.company_id, 'run_update_currency'):
                # currency_rate_live installed
                self.env.companies.sudo().run_update_currency()
        return currency

    @api.model
    @tools.ormcache('code')
    def get_country_by_code(self, code=None):
        """Returns country record by country ISO code."""
        if not code:
            raise UserError(_("Empty country code"))
        RC = self.env['res.country'].with_context()
        country_id = RC.search([('code', '=', code)], limit=1)
        if not country_id:
            raise UserError(_("Unknown country code %s") % code)
        return country_id

    @api.model
    @tools.ormcache('code', 'country_id')
    def get_state_by_code(self, code=None, country_id=None):
        """Returns state record by country and state ISO code."""
        if not code:
            raise UserError(_("Empty state code"))
        if not country_id:
            raise UserError(_("Empty country id"))
        return self.env['res.country.state'].search([('code', '=', code), ('country_id', '=', country_id)], limit=1)

    @api.model
    def browse_ext_id(self, model, external_id):
        return self.env[model].with_context(active_test=False).search([
            ('external_id', '=', external_id)
        ], limit=1)

    @api.model
    def search_ext_ids(self, model, external_ids):
        return self.env[model].with_context(active_test=False).search([('external_id', 'in', external_ids)])

