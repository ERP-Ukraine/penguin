import logging

from collections import defaultdict

from odoo import api, models

_logger = logging.getLogger(__name__)


class ProductNotFound(Exception):
    """Raised when SO product not found"""
    pass


class SaleOrderTransfer(models.AbstractModel):
    _name = 'sale.order.transfer'
    _inherit = 'db.transfer.mixin'
    _description = 'Sale Order Transfer'

    @api.model
    def get_prepared_so_vals(self, row):
        vals = self.get_prepared_vals(row)

        utils = self.env['transfer.utils']
        vals.update({
            'partner_id': utils.browse_ext_id('res.partner', vals['partner_id']).id,
            'partner_shipping_id': utils.browse_ext_id('res.partner', vals['partner_shipping_id']).id,
            'partner_invoice_id': utils.browse_ext_id('res.partner', vals['partner_invoice_id']).id,
            'company_id': utils.browse_ext_id('res.company', vals['company_id']).id
        })
        return vals

    @api.model
    def get_prepared_sol_vals(self, row, taxes_dict, variant_combination_dict):
        vals = self.get_prepared_vals(row)

        utils = self.env['transfer.utils']
        tax_ids = []
        tax_id = taxes_dict.get(vals['tax_id'], False)
        if tax_id:
            tax_ids.append(tax_id)
        # 1. check if product with passing external id exist
        product_id = utils.browse_ext_id('product.product', vals['product_id']).id
        if not product_id:
            # 2. check if product variant combination exist
            sql = '''
                SELECT string_agg(pp.product_tmpl_id || ',' || pav.attribute_id || ',' || pav.name, 
                                  ',' ORDER BY pav.attribute_id, pav.name) combo_id
                FROM product_product pp
                JOIN product_attribute_value_product_product_rel pavppr ON pp.id = pavppr.product_product_id
                JOIN product_attribute_value pav ON pavppr.product_attribute_value_id = pav.id
                WHERE pp.id = %s
                GROUP BY pp.product_tmpl_id, pp.id
            ''' % vals['product_id']
            variant_rows = self.fetch(sql)
            if not variant_rows:
                raise ProductNotFound
            variant = variant_rows[0]
            product_id = variant_combination_dict.get(variant['combo_id'])
            if not product_id:
                raise ProductNotFound
        vals.update({
            'company_id': utils.browse_ext_id('res.company', vals['company_id']).id,
            'product_id': product_id,
            'currency_id': utils.get_currency_by_code(vals['currency_id']).id,
            'tax_id': [(6, 0, tax_ids)]
        })
        return vals

    @api.model
    def transfer_data(self):
        tmpl = '%s: %%s' % self._description
        _logger.info(tmpl, 'import begin!')

        AT = self.env['account.tax']
        # (penguin db tax id, new db tax name)
        taxes_list = ((13, 'TVA due a 7.7% (TN)'), (19, 'TVA due a 0% (Exportations)'),
                      (35, '19% Umsatzsteuer'), (43, 'TVA due à 7.7% (Incl. TN)'),
                      (40, '7% Umsatzsteuer EU Lieferung'), (42, 'TVA due a 7.7% (TN)'),
                      (30, 'Steuerfreie innergem. Lieferung (§4 Abs. 1b UStG)'), (14, 'TVA due à 7.7% (Incl. TN)'),
                      (39, '19 % Umsatzsteuer EU Lieferung'))
        taxes_dict = {t[0]: AT.search([('name', '=', t[1])], limit=1).id for t in taxes_list}

        # select all active sale orders
        sql = '''
            SELECT so.name, so.id external_id, so.partner_id, so.partner_invoice_id, 
                   so.partner_shipping_id, so.company_id,
                   CASE
                       WHEN so.state IN ('future_sale', 'future_sale_confirmation') THEN so.state
                       ELSE 'done'
                    END state
            FROM sale_order so
            JOIN res_partner rp ON so.partner_id = rp.id
            WHERE state != 'draft' AND rp.active IS TRUE;
        '''
        so_rows = self.fetch(sql)

        # select all sale order with active products
        sql = '''
            SELECT sol.id external_id, sol.order_id, sol.qty_to_invoice, sol.price_unit, sol.product_uom_qty,
                   sol.qty_invoiced, sol.price_tax, sol.company_id, sol.price_subtotal,
                   sol.discount, sol.price_reduce, sol.qty_delivered, sol.price_total,
                   sol.product_id, sol.price_reduce_taxexcl, sol.price_reduce_taxinc, rc.name currency_id,
                   atsolr.account_tax_id tax_id
            FROM sale_order_line sol
            JOIN sale_order so ON sol.order_id = so.id
            JOIN product_product pp ON sol.product_id = pp.id
            JOIN res_currency rc ON sol.currency_id = rc.id
            LEFT JOIN account_tax_sale_order_line_rel atsolr ON sol.id = atsolr.sale_order_line_id
            WHERE so.state != 'draft' AND pp.active IS TRUE;
        '''
        sol_rows = self.fetch(sql)

        # select all product variant combination
        sql = '''
            SELECT string_agg(pt.external_id || ',' || pa.external_id::CHAR || ',' || pav.name, 
                              ',' ORDER BY pa.external_id, pav.name) combo_id,
                   pp.id product_id
            FROM product_variant_combination pvc
            JOIN product_product pp ON pvc.product_product_id = pp.id
            JOIN product_template pt ON pp.product_tmpl_id = pt.id
            JOIN product_template_attribute_value ptav ON pvc.product_template_attribute_value_id = ptav.id
            JOIN product_attribute pa ON ptav.attribute_id = pa.id
            JOIN product_attribute_value pav ON ptav.product_attribute_value_id = pav.id
            WHERE pt.external_id NOTNULL and pa.external_id NOTNULL
            GROUP BY pt.external_id, pp.id;
        '''
        self.env.cr.execute(sql)
        combination_rows = self.env.cr.dictfetchall()
        _logger.info(tmpl % 'group combination by product tmpl external id and attr values')
        variant_combination_dict = {r['combo_id']: r['product_id'] for r in combination_rows}

        # group sale order lines by external order id
        sol_grouped_dict = defaultdict(list)
        _logger.info(tmpl % 'group sale order lines by order id; len="%s"', len(sol_rows))
        for idx, sol in enumerate(sol_rows, 1):
            try:
                vals = self.get_prepared_sol_vals(sol, taxes_dict, variant_combination_dict)
            except ProductNotFound:
                warn_msg = tmpl % ('product not found, SOL was skipped; '
                                   'product external_id="%s", SOL external_id="%s", SO external_id="%s"')
                _logger.warning(warn_msg, sol['product_id'], sol['external_id'], sol['order_id'])
                continue
            order_id = vals.pop('order_id')
            sol_grouped_dict[order_id].append(vals)
            if not idx % 200:
                _logger.info(tmpl % 'processed %s sale order lines', idx)
        _logger.info(tmpl, 'all sale order lines was grouped')
        _logger.info(tmpl, '1. prepare defaultdict with key as company id and product recordset as value')
        PP = self.env['product.product']
        product_ids = PP.search([])
        product_company_dict = defaultdict(lambda: PP)
        for p in product_ids:
            product_company_dict[p.company_id.id] |= p

        _logger.info(tmpl, '2. clear company information for all products')
        product_ids.write({'company_id': False})

        _logger.info(tmpl % '3. create sale orders; len="%s"', len(so_rows))
        SO = self.env['sale.order']
        so_dict = {so.external_id: so for so in SO.search([])}
        for idx, so in enumerate(so_rows, 1):
            vals = self.get_prepared_so_vals(so)
            _logger.debug(tmpl % 'prepared SO vals: %s', vals)
            sol_list = sol_grouped_dict.get(vals['external_id'], [])
            _logger.debug(tmpl % 'prepared SOL vals: %s', sol_list)
            so_id = so_dict.get(vals['external_id'])
            if so_id:
                _logger.debug(tmpl % 'found SO with external id "%s"', so_id.external_id)
                so_id.write({
                    **vals,
                    'order_line': [(0, 0, sol_vals) for sol_vals in sol_list]
                })
                _logger.debug(tmpl % 'vals written to SO; id="%s", external_id="%s"', so_id.id, so_id.external_id)
            else:
                so_id = SO.with_context(allowed_company_ids=[vals['company_id']]).create({
                    **vals,
                    'order_line': [(0, 0, sol_vals) for sol_vals in sol_list]
                })
                _logger.debug(tmpl % 'SO created; id="%s", external_id="%s"', so_id.id, so_id.external_id)
            if not idx % 200:
                _logger.info(tmpl % 'processed %s sale orders', idx)

        _logger.info(tmpl, '4. bring product company information back')
        for company_id, product_ids in product_company_dict.items():
            product_ids.write({'company_id': company_id})