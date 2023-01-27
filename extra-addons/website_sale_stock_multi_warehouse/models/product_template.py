from odoo import models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def _get_combination_info(self, combination=False, product_id=False, add_qty=1, pricelist=False, parent_combination=False, only_template=False):
        warehouse_ids = self.env['website'].get_current_website().sudo().warehouse_ids.ids
        combination_info = super(ProductTemplate, self.with_context(warehouse=warehouse_ids))._get_combination_info(
            combination=combination, product_id=product_id, add_qty=add_qty, pricelist=pricelist,
            parent_combination=parent_combination, only_template=only_template)

        if not self.env.context.get('website_sale_stock_get_quantity'):
            return combination_info

        if combination_info['product_id']:
            ProductSu = self.env['product.product'].sudo().with_context(warehouse=warehouse_ids)
            product = ProductSu.browse(combination_info['product_id'])
            product.invalidate_cache(['free_qty', 'virtual_available'])
            combination_info['free_qty'] = product.free_qty
            virtual_available = product.virtual_available
            combination_info['virtual_available'] = virtual_available
            combination_info['virtual_available_formatted'] = self.env['ir.qweb.field.float'].value_to_html(
                virtual_available,
                {'decimal_precision': 'Product Unit of Measure'}
            )
        return combination_info
