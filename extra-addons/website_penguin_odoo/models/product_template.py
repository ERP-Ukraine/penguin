from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    def _get_own_attribute_exclusions(self, combination_ids=None):
        self.ensure_one()
        vals = super()._get_own_attribute_exclusions(combination_ids)
        product_template_attribute_values = self.valid_product_template_attribute_line_ids.product_template_value_ids

        for ptav in product_template_attribute_values:
            for var in ptav.ptav_product_variant_ids:
                if var.sudo().qty_available < 1 and ptav.attribute_line_id.value_count > 1:
                    vals[ptav.id] += [item.id for item in var.product_template_attribute_value_ids if item.id not in ptav.ids and item.attribute_line_id.value_count > 1]
                    
        return vals
