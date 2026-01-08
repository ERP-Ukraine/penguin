from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    def _get_own_attribute_exclusions(self, combination_ids=None):
        self.ensure_one()
        vals = super()._get_own_attribute_exclusions(combination_ids)
        product_template_attribute_lines = (
            self.valid_product_template_attribute_line_ids
        )
        for ptal in product_template_attribute_lines:
            if all(
                [
                    True if qty < 1 else False
                    for qty in ptal.product_template_value_ids.ptav_product_variant_ids.mapped(
                        'qty_available'
                    )
                ]
            ) and any(
                [
                    True if value_count > 1 else False
                    for value_count in ptal.product_template_value_ids.attribute_line_id.mapped(
                        'value_count'
                    )
                ]
            ):
                for ptav in ptal.product_template_value_ids:
                    for var in ptav.ptav_product_variant_ids:
                        vals[ptav.id] += [
                            item.id
                            for item in var.product_template_attribute_value_ids
                            if item.id not in ptav.ids
                            and item.attribute_line_id.value_count > 1
                        ]
        return vals
