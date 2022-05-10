# -*- coding: utf-8 -*-patch
from odoo.addons.mail.tests.common import mail_new_test_user
from odoo.addons.website.tools import MockRequest
from odoo.tests import HOST
from odoo.tests.common import HttpCase


class TestPricelistAfterLogin(HttpCase):

    def setUp(self):
        super().setUp()
        self.domain = 'http://' + HOST
        self.website = self.env['website'].create({
            'name': 'Test Price after Login',
            'domain': self.domain,
        })
        self.product = self.env['product.product'].create({
            'name': 'test_formation',
            'type': 'consu',
            'list_price': 100,
        })
        self.pricelist = self.env['product.pricelist'].create({
            'name': 'Special Pricelist',
            'currency_id': self.env.company.currency_id.id,
            'item_ids': [(0, 0, {
                'compute_price': 'percentage',
                'base': 'list_price',
                'percent_price': 20,
                'applied_on': '3_global',
                'name': 'Basic discount'
            })]
        })
        self.public_user = self.env.ref('base.public_user')
        self.public_partner = self.env.ref('base.public_partner')
        mail_new_test_user(self.env, login='test@mail.com', password='test')
        self.partner = self.env['res.partner'].search([('email', '=', 'test@mail.com')], limit=1)
        self.user = self.partner.user_ids[0]
        self.partner.property_product_pricelist = self.pricelist

    def test_pricelist_after_login(self):
        sale_order = self.env['sale.order'].create({
            'partner_id': self.env.ref('base.res_partner_2').id,
            'user_id': self.public_user.id,
            'website_id': self.website.id,
        })

        sale_order_line = self.env['sale.order.line'].create({
            'product_id': self.product.id,
            'price_unit': 100.00,
            'product_uom': self.env.ref('uom.product_uom_unit').id,
            'product_uom_qty': 2.0,
            'order_id': sale_order.id,
            'name': 'sales order line',
        })

        with MockRequest(self.env, website=self.website, sale_order_id=sale_order.id):
            # testing pricelist before logining
            so = self.website.sale_get_order()
            self.assertNotEqual(so.pricelist_id.id, self.pricelist.id)
            so.write({'partner_id': self.partner.id, 'user_id': self.user.id})

            # testing pricelist after changing user (same as logining)
            self.env.user = self.user
            so = self.website.sale_get_order()
            self.assertEqual(so.pricelist_id.id, self.pricelist.id)
