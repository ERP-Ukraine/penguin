# -*- coding: utf-8 -*-
import logging
import base64
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

START_IDX = 0
END_IDX = 8

_logger = logging.getLogger(__name__)


class NewProductImport(models.TransientModel):
    _name = 'new.product.import.penguin'
    _description = 'Import New Products'

    product_category_id = fields.Many2one('product.category', required=True, string='Product Category')
    seller_id = fields.Many2one('res.partner', required=True, string='Vendor')
    washing_instruction_id = fields.Many2one('product.washing.instruction', string='Washing Instruction')
    material_id = fields.Many2one('product.material', string='Material')
    xls_file = fields.Binary(string='XLS File', required=True, attachment=False)

    @api.constrains('washing_instruction_id', 'material_id',
                    'product_category_id', 'seller_id')
    def _check_provided_fields(self):
        for rec in self:
            if not rec.seller_id:
                raise ValidationError(_('You need yo set seller '
                                        'for new products!'))
            if not rec.product_category_id:
                raise ValidationError(_('You need yo set product category '
                                        'for new products!'))

    def _parse_file(self):
        """Returns generator of xls row as list of columns."""
        file_data = base64.b64decode(self.xls_file)
        base_import = self.env['base_import.import'].create({'file': file_data})
        data = base_import._read_xls(options=None)
        header = next(data)
        while header[START_IDX] != 'Nr.' and header[END_IDX] != 'Total FOB':
            try:
                header = next(data)
            except StopIteration:
                raise ValidationError(
                    _('Headers not found! '
                      '"Nr." expected to be in 1st column and '
                      '"Total FOB" expected to be in 9th column.'))
        return data

    def _convert_attr_to_dict(self, attribute):
        ProductAttribute = self.env['product.attribute']
        PAV = self.env['product.attribute.value']
        product_attr = ProductAttribute.search([('name', '=', attribute)], limit=1)
        if not product_attr:
            raise ValidationError(_('Attribute "%s" doesn\'t exist. '
                                    'Create it and try again.') % attribute)
        attr_list = PAV.search_read([('attribute_id', '=', product_attr.id)], ['name'])
        return {attr['name']: attr['id'] for attr in attr_list}, product_attr.id

    def _get_product_template_attribute_value(self, product_attribute_value, model):
        return model.valid_product_template_attribute_line_ids.filtered(
            lambda l: l.attribute_id == product_attribute_value.attribute_id
        ).product_template_value_ids.filtered(
            lambda v: v.product_attribute_value_id == product_attribute_value)

    def import_new_products(self):
        """Import file, create new products."""
        self = self.with_context(lang='en_US')
        data = self._parse_file()
        ProductTemplate = self.env['product.template']
        ProductProduct = self.env['product.product']
        PAV = self.env['product.attribute.value']
        PTAL = self.env['product.template.attribute.line']
        Seller = self.env['product.supplierinfo']
        product_templates = ProductTemplate

        colors, color_id = self._convert_attr_to_dict('Color')
        sizes, size_id = self._convert_attr_to_dict('Size')

        import_currency = next(data)[END_IDX - 1]
        currency = self.env['res.currency'].search([('name', '=', import_currency)], limit=1)
        if not currency:
            raise ValidationError(
                _('No such currency %s or currency is not set! '
                  'Please set currency under "FOB" column') % import_currency)

        for row in data:
            _logger.debug(row)

            # check if current product barcode exists
            product_with_barcode = ProductProduct.search([('barcode', '=', row[5])])
            if product_with_barcode:
                raise ValidationError(_('Product with barcode "%s" already exists '
                                        'in database with name "%s", please change barcode '
                                        'and try again!') % (row[5], product_with_barcode.name))
            pt_name = '%s %s' % (row[1], row[2])
            gender = 'male' if row[1].lower() in ('men', 'male') else 'female'
            seller_info = {
                'name': self.seller_id.id,
                'currency_id': currency.id,
                'price': row[7],
                'min_qty': 1.0,
            }
            if row[3] in colors:
                color = PAV.browse(colors[row[3]])
            else:
                raise ValidationError(_('You need to create color "%s" '
                                         'before importing new products') % row[3])

            if row[4] in sizes:
                size = PAV.browse(sizes[row[4]])
            else:
                raise ValidationError(_('You need to create size "%s" '
                                        'before importing new products') % row[4])

            product_template = ProductTemplate.search([('name', '=', pt_name)], limit=1)
            if product_template:
                seller = product_template.seller_ids
                if seller:
                    seller.write(seller_info)
                else:
                    seller = Seller.create(seller_info)
                product_template.write({
                    'categ_id': self.product_category_id.id,
                    'washing_instruction_id': self.washing_instruction_id.id,
                    'material_id': self.material_id.id,
                    'seller_ids': [(4, seller.id)]
                })
                color_ptal = PTAL.search([('product_tmpl_id', '=', product_template.id),
                                          ('attribute_id', '=', color_id)])
                size_ptal = PTAL.search([('product_tmpl_id', '=', product_template.id),
                                         ('attribute_id', '=', size_id)])
                if color_ptal:
                    color_ptal.write({'attribute_id': color_id,
                                      'value_ids': [(4, color.id)]})
                else:
                    PTAL.create({'product_tmpl_id': product_template.id,
                                 'attribute_id': color_id,
                                 'value_ids': [(4, color.id)]})
                if size_ptal:
                    size_ptal.write({'attribute_id': size_id,
                                     'value_ids': [(4, size.id)]})
                else:
                    PTAL.create({'product_tmpl_id': product_template.id,
                                 'attribute_id': size_id,
                                 'value_ids': [(4, size.id)]})
            else:
                product_template = ProductTemplate.create({
                    'name': pt_name,
                    'categ_id': self.product_category_id.id,
                    'washing_instruction_id': self.washing_instruction_id.id,
                    'material_id': self.material_id.id,
                    'gender': gender,
                    'seller_ids': [(0, 0, seller_info)],
                    'attribute_line_ids': [
                        (0, 0, {
                            'attribute_id': size_id,
                            'value_ids': [(6, 0, [size.id])]}),
                        (0, 0, {
                            'attribute_id': color_id,
                            'value_ids': [(6, 0, [color.id])]})
                    ]})
            color_attr = self._get_product_template_attribute_value(color, product_template)
            size_attr = self._get_product_template_attribute_value(size, product_template)
            product_product = product_template._get_variant_for_combination(color_attr + size_attr)
            product_product.write({
                'barcode': row[5],
                'default_code': row[0],
                'standard_price': row[7] if currency == self.env.company.currency_id else 0.0,
            })
            product_templates |= product_template

        return {
            'name': _('Imported Products'),
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'product.template',
            'domain': [('id', 'in', product_templates.ids)],
            'views': [(self.env.ref('product.product_template_tree_view').id, 'tree'), 
                      (self.env.ref('product.product_template_only_form_view').id, 'form')],
        }
