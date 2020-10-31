# -*- coding: utf-8 -*-
import base64

from odoo import _, fields, models
from odoo.exceptions import ValidationError
from odoo.tests.common import Form

ARTICLE_IDX = 1
QTY_IDX = 6


class PreOrderImport(models.TransientModel):
    _name = 'sale.penguin.preorder.import'
    _description = 'Import pre-Order from xls file'

    partner_id = fields.Many2one('res.partner', string='Customer', required=True)
    commitment_date = fields.Date(string='Planned Delivery Date')
    xls_file = fields.Binary(string='XLS File', required=True, attachment=False)


    def _parse_file(self):
        """Returns generator of xls row as list of columns."""
        file_data = base64.b64decode(self.xls_file)
        base_import = self.env['base_import.import'].create({'file': file_data})
        data = base_import._read_xls(options=None)
        header = next(data)
        if header[ARTICLE_IDX] != 'Nr.' or header[QTY_IDX] != 'Stückzahlen':
            raise ValidationError(
                _('Wrong file header! '
                  '"Nr." expected to be in 2nd column and '
                  '"Stückzahlen" expected to be in 7th column.'))
        return data

    def _get_product_articles(self):
        """Returns dict of product code as a key and id as a value."""
        recs = self.env['product.product'].search_read([('default_code', '!=', False)],
                                                       ['default_code'])
        return {rec['default_code']: rec['id'] for rec in recs}

    def import_preorder(self):
        """Import file, create pre-Order."""
        data = self._parse_file()
        products_by_code = self._get_product_articles()
        so_form = Form(self.env['sale.order'])
        so_form.partner_id = self.partner_id
        if self.commitment_date:
            so_form.commitment_date = self.commitment_date
        for row in data:
            if all(not col for col in row[:3]):
                # End of table
                break
            if not row[QTY_IDX]:
                continue
            product_id = int(products_by_code.get(row[ARTICLE_IDX], 0))
            if not product_id:
                raise ValidationError(
                    _('Unable to find product for article "%s"') % (row[ARTICLE_IDX],))
            with so_form.order_line.new() as line_form:
                qty = float(row[QTY_IDX])
                line_form.product_id = self.env['product.product'].browse(product_id)
                line_form.product_uom_qty = float(qty)
        if so_form.order_line:
            so_form.save()
            return {
                'name': _('pre-Order'),
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'sale.order',
                'res_id': so_form.id,
                'view_id': self.env.ref('sale.view_order_form').id,
            }
