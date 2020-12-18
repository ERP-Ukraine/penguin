# -*- coding: utf-8 -*-
from odoo import api, fields, models


class Users(models.Model):
    _inherit = 'res.users'

    def _set_industry_field(self):
        chf_id = self.env.ref('base.CHF').id
        swiss_industry = self.env.ref('base_penguin.industry_online_cust_swiss')
        europe_industry = self.env.ref('base_penguin.industry_online_cust_europe')
        done_users = self.env['res.users']
        for user in self:
            if not user.share:
                continue
            partner = user.partner_id
            country_id = partner.country_id
            pricelist_id = partner.property_product_pricelist
            if not any((country_id, pricelist_id)):
                continue
            if country_id and country_id.code == 'CH' or \
                pricelist_id and pricelist_id.currency_id.id == chf_id:
                partner.industry_id = swiss_industry.id
            else:
                partner.industry_id = europe_industry.id
            done_users |= user
        return done_users

    @api.model_create_multi
    def create(self, vals_list):
        users = super(Users, self).create(vals_list)
        with self.env.cr.savepoint():
            users._set_industry_field()
        return users
