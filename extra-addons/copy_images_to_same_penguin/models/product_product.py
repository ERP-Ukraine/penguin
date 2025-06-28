from odoo import models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def action_copy_images_to_same(self):
        self.ensure_one()
        context = {'default_product_id': self.id}

        # manually generated external id of color attr
        color_attr = self.env.ref('__export__.product_attribute_6_deea0cf6', raise_if_not_found=False)
        if color_attr and color_attr in self.mapped('product_template_attribute_value_ids.attribute_id'):
            context['default_attribute_id'] = color_attr.id

        return {
            'name': 'Copy images to same',
            'type': 'ir.actions.act_window',
            'res_model': 'product.product.same.images',
            'view_mode': 'form',
            'target': 'new',
            'context': context,
        }
