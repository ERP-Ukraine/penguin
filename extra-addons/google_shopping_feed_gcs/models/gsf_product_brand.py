# -*- coding: utf-8 -*-
#!/usr/bin/python3
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import json, requests, logging
from werkzeug import urls   
from odoo import models, fields, api, _
from odoo.exceptions import Warning, UserError
_logger = logging.getLogger(__name__)

class ProductBrandGSF(models.Model):
    _name = "product.brand.gsf"
    _description = "Product Brand"
    
    name = fields.Char("Brand Name", help="Product brand")