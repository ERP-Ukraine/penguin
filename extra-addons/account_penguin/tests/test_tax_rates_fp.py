from odoo import fields
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

# +───────────────────────────────────────────────────────────+─────────────+────────────────────+─────────+────────+
# | Description                                               | Unit Price  | Tax rate           | Base    | Tax    |
# +───────────────────────────────────────────────────────────+─────────────+────────────────────+─────────+────────+
# | Product with defaults                                     | 250.00      | 7.7% VAT included  | 232.13  | 17.87  |
# | Odoo way (19% incl applied to product with 7.7% incl)     | 276.23      | 19% vat included   | 232.13  | 44.10  |
# | Penguin way (19% incl applied to product with 7.7% incl)  | 250.00      | 19% vat included   | 210.08  | 39.92  |
# | Odoo way (0% incl applied to product with 7.7% incl)      | 232.13      | 0% vat included    | 232.13  | 0.00   |
# | Penguin way (0% incl applied to product with 7.7% incl)   | 232.13      | 0% vat included    | 232.13  | 0.00   |
# +───────────────────────────────────────────────────────────+─────────────+────────────────────+─────────+────────+
# Odoo keeps Base the same. Penguin keeps unit price the same until we have zero vat case.


@tagged('post_install', '-at_install')
class PenguinTaxes(TransactionCase):

    def setUp(self):
        super().setUp()
        self.fiscal_position_model = self.env['account.fiscal.position']
        self.fiscal_position_tax_model = self.env['account.fiscal.position.tax']
        self.tax_model = self.env['account.tax']
        self.product_tmpl_model = self.env['product.template']

        self.tax_include_77 = self.tax_model.create({
            'name': "Include 7.7%",
            'amount': 7.70,
            'amount_type': 'percent',
            'price_include': True})
        self.tax_include_19 = self.tax_model.create({
            'name': "Include 19%",
            'amount': 19.0,
            'amount_type': 'percent',
            'price_include': True})
        self.tax_include_0 = self.tax_model.create({
            'name': "Include 0%",
            'amount': 0.0,
            'amount_type': 'percent',
            'price_include': True})
        self.product_tmpl_a = self.product_tmpl_model.create({
            'name': "Jacket",
            'list_price': 250,
            'taxes_id': [(6, 0, [self.tax_include_77.id])]})
        self.product_a = self.product_tmpl_a.product_variant_id
        self.fpos_77_19 = self.fiscal_position_model.create({
            'name': "7.7 incl -> 19 incl",
            'sequence': 1})
        self.fiscal_position_tax_model.create({
            'position_id': self.fpos_77_19.id,
            'tax_src_id': self.tax_include_77.id,
            'tax_dest_id': self.tax_include_19.id})
        self.fpos_77_0 = self.fiscal_position_model.create({
            'name': "7.7 incl -> 0 incl",
            'sequence': 2})
        self.fiscal_position_tax_model.create({
            'position_id': self.fpos_77_0.id,
            'tax_src_id': self.tax_include_77.id,
            'tax_dest_id': self.tax_include_0.id})

    def test_fp_application_penguin_way(self):
        currency = self.env.company.currency_id
        unit_price = self.product_a._get_tax_included_unit_price(
            self.env.company,
            self.env.company.currency_id,
            fields.Date.today(),
            'sale',
            product_price_unit=250.0,
            product_taxes=self.product_a.taxes_id,
            fiscal_position=self.fpos_77_0)
        self.assertAlmostEqual(unit_price, 232.13, currency.decimal_places)
        unit_price = self.product_a._get_tax_included_unit_price(
            self.env.company,
            self.env.company.currency_id,
            fields.Date.today(),
            'sale',
            product_price_unit=250.0,
            product_taxes=self.product_a.taxes_id,
            fiscal_position=self.fpos_77_19)
        self.assertAlmostEqual(unit_price, 250.00, currency.decimal_places)
