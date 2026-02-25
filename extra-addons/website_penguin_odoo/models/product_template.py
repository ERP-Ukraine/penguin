from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    def _get_own_attribute_exclusions_custom(self, combination_ids=None):
        self.ensure_one()
        vals = super()._get_own_attribute_exclusions(combination_ids)
        product_template_attribute_values = self.valid_product_template_attribute_line_ids.product_template_value_ids

        for ptav in product_template_attribute_values:
            for var in ptav.ptav_product_variant_ids:
                if var.sudo().qty_available < 1 and ptav.attribute_line_id.value_count > 1:
                    vals[ptav.id] += [item.id for item in var.product_template_attribute_value_ids if item.id not in ptav.ids and item.attribute_line_id.value_count > 1]
                    
        return vals

    def _get_attribute_exclusions_custom(self, parent_combination=None, parent_name=None, combination_ids=None):
        self.ensure_one()
        parent_combination = parent_combination or self.env['product.template.attribute.value']
        archived_products = self.with_context(active_test=False).product_variant_ids.filtered(lambda l: not l.active)
        active_combinations = set(tuple(product.product_template_attribute_value_ids.ids) for product in self.product_variant_ids)
        return {
            'exclusions': self._complete_inverse_exclusions(
                self._get_own_attribute_exclusions_custom(combination_ids=combination_ids)
            ),
            'archived_combinations': list(set(
                tuple(product.product_template_attribute_value_ids.ids)
                for product in archived_products
                if product.product_template_attribute_value_ids and all(
                    ptav.ptav_active or combination_ids and ptav.id in combination_ids
                    for ptav in product.product_template_attribute_value_ids
                )
            ) - active_combinations),
            'parent_exclusions': self._get_parent_attribute_exclusions(parent_combination),
            'parent_combination': parent_combination.ids,
            'parent_product_name': parent_name,
            'mapped_attribute_names': self._get_mapped_attribute_names(parent_combination),
        }

    def _is_combination_possible_custom(self, combination, parent_combination=None, ignore_no_variant=False):
        res = super()._is_combination_possible(combination, parent_combination, ignore_no_variant)
        if res and combination:
            ptav_ids = combination.ids
            exclusions = self._get_own_attribute_exclusions_custom()
            for ptav_id in ptav_ids:
                if exclusions.get(ptav_id) and any([p_id in exclusions[ptav_id] for p_id in ptav_ids if p_id != ptav_id]):
                    return False
        return res

    def _get_combination_info(
        self, combination=False, product_id=False, add_qty=1.0,
        parent_combination=False, only_template=False,
    ):
        res = super()._get_combination_info(combination, product_id, add_qty, parent_combination, only_template)
        combination = combination or self.env['product.template.attribute.value']
        parent_combination = parent_combination or self.env['product.template.attribute.value']

        if not product_id and not combination and not only_template:
            combination = self._get_first_possible_combination(parent_combination)

        if only_template:
            product = self.env['product.product']
        elif product_id:
            product = self.env['product.product'].browse(product_id)
            if (combination - product.product_template_attribute_value_ids):
                # If the combination is not fully represented in the given product
                #   make sure to fetch the right product for the given combination
                product = self._get_variant_for_combination(combination)
        else:
            product = self._get_variant_for_combination(combination)

        combination = combination or product.product_template_attribute_value_ids
        res['is_combination_possible'] = self._is_combination_possible_custom(combination=combination, parent_combination=parent_combination)
        return res
