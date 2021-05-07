# -*- coding: utf-8 -*-
from odoo import api, models


class Partner(models.Model):
    _inherit = 'res.partner'

    @api.model_create_multi
    def create(self, vals_list):
        chf = self.env.ref('base.CHF')
        switzerland = self.env.ref('base.ch')
        swiss_industry = self.env.ref('base_penguin.industry_online_cust_swiss')
        europe_industry = self.env.ref('base_penguin.industry_online_cust_europe')
        updated_vals_list = []
        for vals in vals_list:
            if vals.get('industry_id'):
                updated_vals_list.append(vals)
                continue
            pricelist_id = vals.get('pricelist_id')
            vals['industry_id'] = europe_industry.id
            if vals.get('country_id', 0) == switzerland.id:
                vals['industry_id'] = swiss_industry.id
            elif pricelist_id:
                pricelist = self.env['product.pricelist'].browse(pricelist_id)
                if pricelist.currency_id == chf:
                    vals['industry_id'] = swiss_industry.id
            updated_vals_list.append(vals)
        return super().create(updated_vals_list)
