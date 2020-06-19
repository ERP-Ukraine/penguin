from odoo import api, models


class ProductAttributeTransfer(models.AbstractModel):
    _name = 'product.attribute.transfer'
    _inherit = 'db.transfer.catalog.mixin'
    _description = 'Product Attribute Transfer'

    @api.model
    def transfer_data(self):
        model = 'product.attribute'
        sql = '''SELECT id external_id, name, sequence, 'dynamic' create_variant FROM product_attribute'''
        log_prefix = self._description
        self._transfer_data(sql, model, log_prefix)


class ProductAttributeValueTransfer(models.AbstractModel):
    _name = 'product.attribute.value.transfer'
    _inherit = 'db.transfer.catalog.mixin'
    _description = 'Product Attribute Value Transfer'

    @api.model
    def get_prepared_vals(self, row):
        vals = super().get_prepared_vals(row)

        utils = self.env['transfer.utils']
        vals['attribute_id'] = utils.browse_ext_id('product.attribute', vals['attribute_id']).id
        # check if attribute id and name already exist
        attr_value_id = self.env['product.attribute.value'].search([
            ('name', '=', vals['name']), ('attribute_id', '=', vals['attribute_id'])
        ])
        # replace external id if attr value already exist
        if attr_value_id:
            vals['external_id'] = attr_value_id.external_id

        return vals

    @api.model
    def transfer_data(self):
        model = 'product.attribute.value'
        sql = 'SELECT id external_id, name, sequence, attribute_id FROM product_attribute_value'
        log_prefix = self._description
        self._transfer_data(sql, model, log_prefix)