# -*- coding: utf-8 -*-
# !/usr/bin/python3
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import models, fields, api, _


class GoogleProductCategoryGCS(models.Model):
    _name = "google.product.category.gcs"
    _desctription = "Google Product Categories GCS"
    _rec_name = 'complete_name'
    _order = 'complete_name'

    name = fields.Char("Category Name", index=True, required=True, copy=False, help="Google category name")
    category_code = fields.Char("Category Code", required=True, copy=False, help="Google category code")
    parent_categ_id = fields.Many2one("google.product.category.gcs", "Parent Category ID", index=True, copy=False,
                                      help="Google parent category")
    complete_name = fields.Char(
        'Complete Name', compute='_compute_complete_name',recursive=True,
        store=True)

    @api.depends('name', 'parent_categ_id.complete_name')
    def _compute_complete_name(self):
        for category in self:
            if category.parent_categ_id:
                category.complete_name = '%s > %s' % (category.parent_categ_id.complete_name, category.name)
            else:
                category.complete_name = category.name
