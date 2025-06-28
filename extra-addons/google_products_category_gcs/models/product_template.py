# -*- coding: utf-8 -*-
# !/usr/bin/python3
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import models, fields


class ProductTemplate(models.Model):
    _inherit = "product.template"

    google_product_category = fields.Many2one("google.product.category.gcs", string="Google Product Category",
                                              help="Select google product category")
