# -*- coding: utf-8 -*-
from odoo import api, fields, models


class Partner(models.Model):
    _inherit = 'res.partner'

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        list_id = self.env.company.contacts_mass_mailing_list.id
        if not list_id:
            return res
        mailing_contacts = [{
            'name': el.name,
            'email': el.email,
            'list_ids': [(4, list_id)]} for el in res]
        with self.env.cr.savepoint():
            self.env['mailing.contact'].create(mailing_contacts)
        return res
