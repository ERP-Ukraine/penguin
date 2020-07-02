import base64
import logging
import os
import re

from odoo import api, fields, models
from odoo.tools import config


_logger = logging.getLogger(__name__)


class ProductWashingInstructionTransfer(models.AbstractModel):
    _name = 'product.washing.instruction.transfer'
    _inherit = 'db.transfer.catalog.mixin'
    _description = 'Product Washing Instruction Transfer'

    @api.model
    def transfer_data(self):
        log_prefix = self._description
        model = 'product.washing.instruction'
        sql = 'SELECT id external_id, name, description FROM washing_instruction'
        self._transfer_data(sql, model, log_prefix)


class ProductMaterialTransfer(models.AbstractModel):
    _name = 'product.material.transfer'
    _inherit = 'db.transfer.catalog.mixin'
    _description = 'Product Material Transfer'

    @api.model
    def transfer_data(self):
        log_prefix = self._description
        model = 'product.material'
        sql = 'SELECT id external_id, name, description FROM material_material'
        self._transfer_data(sql, model, log_prefix)


class ProductFeatureTransfer(models.AbstractModel):
    _name = 'product.feature.transfer'
    _inherit = 'db.transfer.catalog.mixin'
    _description = 'Product Feature Transfer'

    @api.model
    def transfer_data(self):
        log_prefix = self._description
        model = 'product.feature'
        sql = 'SELECT id external_id, name FROM product_feature'
        self._transfer_data(sql, model, log_prefix)


class ProductPublicCategoryTransfer(models.AbstractModel):
    _name = 'product.public.category.transfer'
    _inherit = 'db.transfer.catalog.mixin'
    _description = 'Product Public Category Transfer'

    @api.model
    def get_prepared_vals(self, row):
        vals = super().get_prepared_vals(row)

        utils = self.env['transfer.utils']
        if vals['parent_id']:
            vals['parent_id'] = utils.browse_ext_id('product.public.category', vals['parent_id']).id

        return vals

    @api.model
    def transfer_data(self):
        log_prefix = self._description
        model = 'product.public.category'
        sql = 'SELECT id external_id, name, parent_id, sequence FROM product_public_category ORDER BY parent_id DESC'
        self._transfer_data(sql, model, log_prefix)


class ParseImageMixin(models.AbstractModel):
    _name = 'parse.image.mixin'
    _description = 'Utils model for image parsing from stored file'

    @api.model
    def _full_path(self, path):
        # sanitize path
        path = re.sub('[.]', '', path)
        path = path.strip('/\\')
        db_name = self.env['ir.config_parameter'].sudo().get_param('database.old.dbname')
        return os.path.join(config.filestore(db_name), path)

    @api.model
    def _file_read(self, fname):
        full_path = self._full_path(fname)
        r = ''
        try:
            with open(full_path, 'rb') as fd:
                r = base64.b64encode(fd.read())
        except (IOError, OSError):
            _logger.info("_read_file reading %s", full_path, exc_info=True)
        return r

    @api.model
    def get_parsed_images(self, rows):
        return {r['external_id']: self._file_read(r['store_fname']) for r in rows}


class ProductTemplateTransfer(models.AbstractModel):
    _name = 'product.template.transfer'
    _inherit = ['db.transfer.mixin', 'parse.image.mixin']
    _description = 'Product Template Transfer'
    
    @api.model
    def get_parsed_features(self, rows):
        utils = self.env['transfer.utils']
        result = {}
        for row in rows:
            feature_ids = utils.search_ext_ids('product.feature', row['feature_ids'])
            result[row['external_id']] = [(6, 0, feature_ids.ids)]
        return result

    @api.model
    def get_parsed_categories(self, rows):
        utils = self.env['transfer.utils']
        result = {}
        for row in rows:
            public_categ_ids = utils.search_ext_ids('product.public.category', row['public_categ_ids'])
            result[row['external_id']] = [(6, 0, public_categ_ids.ids)]
        return result

    @api.model
    def get_prepared_vals(self, row):
        vals = super().get_prepared_vals(row)
        utils = self.env['transfer.utils']
        vals.update({
            'categ_id': utils.browse_ext_id('product.category', vals['categ_id']).id,
            'material_id': utils.browse_ext_id('product.material', vals['material_id']).id,
            'washing_instruction_id': utils.browse_ext_id('product.washing.instruction',
                                                          vals['washing_instruction_id']).id
        })
        return vals

    @api.model
    def transfer_data(self):
        tmpl = '%s: %%s' % self._description
        _logger.info(tmpl, 'import begin!')

        # select active products
        sql = '''
            SELECT id external_id, name, sale_ok, purchase_ok, type, hs_code, categ_id, washing_instruction_id,
                   material_id, gender, list_price, purchase_method, description_sale website_sale_description, 
                   description_purchase, description_picking, tracking, website_published, '' description_sale
            FROM product_template
            WHERE active IS TRUE;
        '''
        rows = self.fetch(sql)
        # select features
        sql = '''
            SELECT product_template_id external_id, array_agg(product_feature_id) feature_ids
            FROM product_feature_product_template_rel
            GROUP BY product_template_id;
        '''
        features_dict = self.get_parsed_features(self.fetch(sql))
        # select product images
        sql = '''
            SELECT res_id external_id, store_fname
            FROM ir_attachment
            WHERE res_model = 'product.template' AND res_field = 'image'
        '''
        images_dict = self.get_parsed_images(self.fetch(sql))

        # select public categories
        sql = '''
            SELECT product_template_id external_id, array_agg(product_public_category_id) public_categ_ids
            FROM product_public_category_product_template_rel pt
            GROUP BY product_template_id
        '''
        public_categories_dict = self.get_parsed_categories(self.fetch(sql))

        PT = self.env['product.template'].sudo()
        product_ids = PT.search([])
        product_dict = {p.external_id: p for p in product_ids}
        _logger.info(tmpl % 'create or update product templates; len="%s"', len(rows))
        for idx, row in enumerate(rows, 1):
            vals = self.get_prepared_vals(row)
            vals.update({
                'feature_ids': features_dict.get(vals['external_id'], False),
                'public_categ_ids': public_categories_dict.get(vals['external_id'], False)
            })
            _logger.debug(tmpl % 'prepared vals %s', vals)
            vals['image_1920'] = images_dict.get(vals['external_id'], False)
            product = product_dict.get(vals['external_id'])

            if product:
                # small performance fix
                if product.image_1920 == vals['image_1920']:
                    vals.pop('image_1920')
                _logger.debug(tmpl % 'found record with external id %s', product.external_id)
                product.write(vals)
                _logger.debug(tmpl % 'vals written; id="%s", external_id="%s"', product.id, product.external_id)
            else:
                product = PT.create(vals)
                _logger.debug(tmpl % 'record created; id="%s", external_id="%s"', product.id, product.external_id)
            if not idx % 20:
                _logger.info(tmpl % 'processed %s products', idx)


class ProductProduct(models.Model):
    _inherit = 'product.product'

    attr_value_names = fields.Char(compute='_compute_attribute_names', store=True, index=True)
    attr_external_ids_concat = fields.Char(compute='_compute_attribute_names', store=True, index=True)

    @api.depends('product_template_attribute_value_ids')
    def _compute_attribute_names(self):
        for rec in self:
            ptav_ids = rec.product_template_attribute_value_ids
            rec.attr_value_names = ','.join(sorted(ptav.name for ptav in ptav_ids))
            rec.attr_external_ids_concat = ','.join(sorted(str(ptav.attribute_id.external_id) for ptav in ptav_ids))


class ProductProductTransfer(models.AbstractModel):
    _name = 'product.product.transfer'
    _inherit = ['db.transfer.mixin', 'parse.image.mixin']
    _description = 'Product Transfer'

    @api.model
    def get_prepared_vals(self, row):
        vals = super().get_prepared_vals(row)

        utils = self.env['transfer.utils']
        vals['product_tmpl_id'] = utils.browse_ext_id('product.template', vals['product_tmpl_id']).id
        return vals

    @api.model
    def create_product_tmpl_attribute_lines(self, vals):
        utils = self.env['transfer.utils']
        PAV = self.env['product.attribute.value']
        PTAL = self.env['product.template.attribute.line']

        attr_value_ids = PAV
        for combination in vals['attr_value_combination']:
            if not combination:
                continue
            value_name, attr_external_id = combination.split(';')
            attr_id = utils.browse_ext_id('product.attribute', int(attr_external_id))
            attr_value_ids |= PAV.search([
                ('attribute_id', '=', attr_id.id), ('name', '=', value_name)
            ])

        combination = PTAL
        for attr_value in attr_value_ids:
            attribute_line_id = PTAL.search([
                ('product_tmpl_id', '=', vals['product_tmpl_id']),
                ('attribute_id', '=', attr_value.attribute_id.id)
            ])
            if not attribute_line_id:
                attribute_line_id = PTAL.create({
                    'product_tmpl_id': vals['product_tmpl_id'],
                    'attribute_id': attr_value.attribute_id.id,
                    'value_ids': [(6, 0, attr_value.ids)]
                })
            if attr_value not in attribute_line_id.value_ids:
                attribute_line_id.value_ids = [(4, attr_value.id)]
            combination |= attribute_line_id

        vals['combination'] = combination.product_template_value_ids.filtered(
            lambda v: v.product_attribute_value_id in attr_value_ids
        )

    @api.model
    def transfer_data(self):
        tmpl = '%s: %%s' % self._description
        _logger.info(tmpl, 'import begin!')
        company_ids = self.env['res.company'].search([])
        self = self.with_context(allowed_company_ids=company_ids.ids)
        # select product variants
        sql = '''
            SELECT pp.id external_id, pp.product_tmpl_id product_tmpl_id, pp.default_code, 
                   description_sale website_sale_description, '' description_sale,
                   array_agg(pav.name || ';' || pav.attribute_id) attr_value_combination
            FROM product_product pp
            LEFT JOIN product_attribute_value_product_product_rel pavppr on pp.id = pavppr.product_product_id
            LEFT JOIN product_attribute_value pav on pavppr.product_attribute_value_id = pav.id
            LEFT JOIN product_template pt on pp.product_tmpl_id = pt.id
            WHERE pp.active IS TRUE
            GROUP BY pp.id, pp.product_tmpl_id, pp.default_code;
        '''
        rows = self.fetch(sql)
        # select product variant images
        sql = '''
            SELECT res_id external_id, store_fname
            FROM ir_attachment
            WHERE res_model = 'product.product' AND res_field = 'image_variant';
        '''
        images_dict = self.get_parsed_images(self.fetch(sql))

        PT = self.env['product.template']
        processed_product_dict = {}
        _logger.info(tmpl % 'create product.template.attribute.line for product.template; len="%s"', len(rows))
        for idx, row in enumerate(rows, 1):
            vals = self.get_prepared_vals(row)
            self.create_product_tmpl_attribute_lines(vals)
            if vals['combination']:
                _logger.debug(tmpl % 'attribute values created, vals="%s"', vals)
            else:
                _logger.debug(tmpl % 'attribute values not found, vals="%s"', vals)
            processed_product_dict[vals['external_id']] = vals
            if not idx % 100:
                _logger.info(tmpl % 'processed %s products', idx)

        _logger.info(tmpl % 'create product variants; len="%s"', len(processed_product_dict.keys()))
        idx = 0
        for external_id, vals in processed_product_dict.items():
            combination = vals.pop('combination')
            attr_value_combination = vals.pop('attr_value_combination')
            product_tmpl_id = PT.browse(vals.pop('product_tmpl_id'))

            _logger.debug(tmpl % 'prepared vals: %s', vals)
            vals['image_variant_1920'] = images_dict.get(vals['external_id'], False)
            if combination:
                _logger.debug(tmpl % 'trying to create combination with %s', combination)
                product_id = product_tmpl_id._create_product_variant(combination)
                if product_id:
                    # small performance fix
                    if vals['image_variant_1920'] in {product_id.image_variant_1920, product_id.image_1920}:
                        vals.pop('image_variant_1920')
                    product_id.write(vals)
                    _logger.debug(tmpl % 'combination created, vals written; id="%s", external_id="%s"',
                                 product_id.id, product_id.external_id)
                else:
                    _logger.debug(tmpl % 'combination not found')
            elif None in attr_value_combination:
                product_id = product_tmpl_id.product_variant_ids[:1]
                _logger.debug(tmpl % 'attributes not found, write vals to default product variant')
                # small performance fix
                if vals['image_variant_1920'] in {product_id.image_variant_1920, product_id.image_1920}:
                    vals.pop('image_variant_1920')
                product_id.write(vals)
                _logger.debug(tmpl % 'vals written; id="%s", external_id="%s"', product_id.id, product_id.external_id)
            else:
                _logger.debug(tmpl % 'combination not found')
            idx += 1
            if not idx % 100:
                _logger.info(tmpl % 'processed %s  products', idx)
