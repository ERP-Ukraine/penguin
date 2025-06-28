# -*- coding: utf-8 -*-
import base64

from odoo import _, fields, models
from odoo.exceptions import ValidationError

ARTICLE_IDX = 1
QTY_IDX = 6


class PreOrderImport(models.TransientModel):
    _name = 'sale.penguin.preorder.import'
    _description = 'Import pre-Order from xls file'

    partner_id = fields.Many2one('res.partner', string='Customer', required=True)
    pricelist_id = fields.Many2one('product.pricelist', string='Pricelist', required=True)
    commitment_date = fields.Date(string='Planned Delivery Date')
    xls_file = fields.Binary(string='XLS File', required=True, attachment=False)

    def _parse_file(self):
        """Returns generator of xls row as list of columns."""
        file_data = base64.b64decode(self.xls_file)
        base_import = self.env['base_import.import'].create({'file': file_data})
        _rows_number, rows = base_import._read_xls(options={})
        headers = rows[0]
        if headers[ARTICLE_IDX] != 'Nr.' or headers[QTY_IDX] != 'Stk.':
            raise ValidationError(
                _('Wrong file header! '
                  '"Nr." expected to be in 2nd column and '
                  '"Stk." expected to be in 7th column.'))
        return rows[1:]

    def _get_product_articles(self):
        """Returns dict of product code as a key and id as a value."""
        recs = self.env['product.product'].search_read([('default_code', '!=', False)],
                                                       ['default_code'])
        return {rec['default_code']: rec['id'] for rec in recs}

    def import_preorder(self):
        """Import file, create pre-Order."""
        data = self._parse_file()
        products_by_code = self._get_product_articles()
        SaleOrder = self.env['sale.order']
        SaleOrderLine = self.env['sale.order.line']
        so_temp = {}
        so_lines_temp = []
        so_temp['partner_id'] = self.partner_id.id
        so_temp['pricelist_id'] = self.pricelist_id.id
        if self.commitment_date:
            so_temp['commitment_date'] = self.commitment_date
            so_temp['date_order'] = self.commitment_date
        for row in data:
            if all(not col for col in row[:3]):
                # End of table
                break
            if not row[QTY_IDX].strip():
                continue
            product_id = int(products_by_code.get(row[ARTICLE_IDX], 0))
            if not product_id:
                raise ValidationError(
                    _('Unable to find product for article "%s"') % (row[ARTICLE_IDX],))
            line_temp = {}
            qty = float(row[QTY_IDX].strip())
            line_temp['product_id'] = self.env['product.product'].browse(product_id).id
            line_temp['product_uom_qty'] = float(qty)
            so_lines_temp.append(line_temp)
        if so_lines_temp:
            sale_order = SaleOrder.create(so_temp)
            for line_temp in so_lines_temp:
                line_temp['order_id'] = sale_order.id
                SaleOrderLine.create(line_temp)

            return {
                'name': _('pre-Order'),
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'sale.order',
                'res_id': sale_order.id,
                'view_id': self.env.ref('sale.view_order_form').id,
            }

