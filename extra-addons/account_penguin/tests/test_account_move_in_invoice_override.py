from odoo.tests import Form
from odoo import fields
from odoo.addons.account.tests.test_account_move_in_invoice import (
    TestAccountMoveInInvoiceOnchanges,
)


# PEN-104 Change tax rate calculation
def test_in_invoice_line_onchange_product_2_with_fiscal_pos(self):
    """Test mapping a price-included tax (10%) with a price-excluded tax (20%) on a price_unit of 110.0.
    The price_unit should be 91.67 after applying the fiscal position.
    """
    tax_price_include = self.env['account.tax'].create(
        {
            'name': '10% incl',
            'type_tax_use': 'purchase',
            'amount_type': 'percent',
            'amount': 10,
            'price_include_override': 'tax_included',
            'include_base_amount': True,
        }
    )
    tax_price_exclude = self.env['account.tax'].create(
        {
            'name': '15% excl',
            'type_tax_use': 'purchase',
            'amount_type': 'percent',
            'amount': 15,
        }
    )

    fiscal_position = self.env['account.fiscal.position'].create(
        {
            'name': 'fiscal_pos_a',
            'tax_ids': [
                (
                    0,
                    None,
                    {
                        'tax_src_id': tax_price_include.id,
                        'tax_dest_id': tax_price_exclude.id,
                    },
                ),
            ],
        }
    )

    product = self.env['product.product'].create(
        {
            'name': 'product',
            'uom_id': self.env.ref('uom.product_uom_unit').id,
            'standard_price': 110.0,
            'supplier_taxes_id': [(6, 0, tax_price_include.ids)],
        }
    )

    move_form = Form(
        self.env['account.move'].with_context(default_move_type='in_invoice')
    )
    move_form.partner_id = self.partner_a
    move_form.invoice_date = fields.Date.from_string('2019-01-01')
    move_form.currency_id = self.other_currency
    move_form.fiscal_position_id = fiscal_position
    with move_form.invoice_line_ids.new() as line_form:
        line_form.product_id = product
    invoice = move_form.save()

    # ERP start
    self.assertInvoiceValues(
        invoice,
        [
            {
                'product_id': product.id,
                'price_unit': 220.0,
                'price_subtotal': 220.0,
                'price_total': 253.0,
                'tax_ids': tax_price_exclude.ids,
                'tax_line_id': False,
                'currency_id': self.other_currency.id,
                'amount_currency': 220.0,
                'debit': 110.0,
                'credit': 0.0,
            },
            {
                'product_id': False,
                'price_unit': 0.0,
                'price_subtotal': 0.0,
                'price_total': 0.0,
                'tax_ids': [],
                'tax_line_id': tax_price_exclude.id,
                'currency_id': self.other_currency.id,
                'amount_currency': 33.0,
                'debit': 16.5,
                'credit': 0.0,
            },
            {
                'product_id': False,
                'price_unit': 0.0,
                'price_subtotal': 0.0,
                'price_total': 0.0,
                'tax_ids': [],
                'tax_line_id': False,
                'currency_id': self.other_currency.id,
                'amount_currency': -253.0,
                'debit': 0.0,
                'credit': 126.5,
            },
        ],
        {
            'currency_id': self.other_currency.id,
            'fiscal_position_id': fiscal_position.id,
            'amount_untaxed': 220.0,
            'amount_tax': 33.0,
            'amount_total': 253.0,
        },
    )
    # ERP end

    uom_dozen = self.env.ref('uom.product_uom_dozen')
    with Form(invoice) as move_form:
        with move_form.invoice_line_ids.edit(0) as line_form:
            line_form.product_uom_id = uom_dozen

    # ERP start
    self.assertInvoiceValues(
        invoice,
        [
            {
                'product_id': product.id,
                'product_uom_id': uom_dozen.id,
                'price_unit': 2640.0,
                'price_subtotal': 2640.0,
                'price_total': 3036.0,
                'tax_ids': tax_price_exclude.ids,
                'tax_line_id': False,
                'currency_id': self.other_currency.id,
                'amount_currency': 2640.0,
                'debit': 1320.0,
                'credit': 0.0,
            },
            {
                'product_id': False,
                'product_uom_id': False,
                'price_unit': 0.0,
                'price_subtotal': 0.0,
                'price_total': 0.0,
                'tax_ids': [],
                'tax_line_id': tax_price_exclude.id,
                'currency_id': self.other_currency.id,
                'amount_currency': 396.0,
                'debit': 198.0,
                'credit': 0.0,
            },
            {
                'product_id': False,
                'product_uom_id': False,
                'price_unit': 0.0,
                'price_subtotal': 0.0,
                'price_total': 0.0,
                'tax_ids': [],
                'tax_line_id': False,
                'currency_id': self.other_currency.id,
                'amount_currency': -3036.0,
                'debit': 0.0,
                'credit': 1518.0,
            },
        ],
        {
            'currency_id': self.other_currency.id,
            'fiscal_position_id': fiscal_position.id,
            'amount_untaxed': 2640.0,
            'amount_tax': 396.0,
            'amount_total': 3036.0,
        },
        # ERP end
    )
    # ERP end


def test_in_invoice_line_onchange_product_2_with_fiscal_pos_2(self):
    """Test mapping a price-included tax (10%) with another price-included tax (20%) on a price_unit of 110.0.
    The price_unit should be 110.01 after applying the fiscal position.
    """
    tax_price_include_1 = self.env['account.tax'].create(
        {
            'name': '10% incl',
            'type_tax_use': 'purchase',
            'amount_type': 'percent',
            'amount': 10,
            'price_include_override': 'tax_included',
            'include_base_amount': True,
        }
    )
    tax_price_include_2 = self.env['account.tax'].create(
        {
            'name': '20% incl',
            'type_tax_use': 'purchase',
            'amount_type': 'percent',
            'amount': 20,
            'price_include_override': 'tax_included',
            'include_base_amount': True,
        }
    )

    fiscal_position = self.env['account.fiscal.position'].create(
        {
            'name': 'fiscal_pos_a',
            'tax_ids': [
                (
                    0,
                    None,
                    {
                        'tax_src_id': tax_price_include_1.id,
                        'tax_dest_id': tax_price_include_2.id,
                    },
                ),
            ],
        }
    )

    product = self.env['product.product'].create(
        {
            'name': 'product',
            'uom_id': self.env.ref('uom.product_uom_unit').id,
            'standard_price': 110.0,
            'supplier_taxes_id': [(6, 0, tax_price_include_1.ids)],
        }
    )

    move_form = Form(
        self.env['account.move'].with_context(default_move_type='in_invoice')
    )
    move_form.partner_id = self.partner_a
    move_form.invoice_date = fields.Date.from_string('2019-01-01')
    move_form.currency_id = self.other_currency
    move_form.fiscal_position_id = fiscal_position
    with move_form.invoice_line_ids.new() as line_form:
        line_form.product_id = product
    invoice = move_form.save()

    # ERP start
    self.assertInvoiceValues(
        invoice,
        [
            {
                'product_id': product.id,
                'price_unit': 220.0,
                'price_subtotal': 183.33,
                'price_total': 220.0,
                'tax_ids': tax_price_include_2.ids,
                'tax_line_id': False,
                'currency_id': self.other_currency.id,
                'amount_currency': 183.33,
                'debit': 91.67,
                'credit': 0.0,
            },
            {
                'product_id': False,
                'price_unit': 0.0,
                'price_subtotal': 0.0,
                'price_total': 0.0,
                'tax_ids': [],
                'tax_line_id': tax_price_include_2.id,
                'currency_id': self.other_currency.id,
                'amount_currency': 36.67,
                'debit': 18.34,
                'credit': 0.0,
            },
            {
                'product_id': False,
                'price_unit': 0.0,
                'price_subtotal': 0.0,
                'price_total': 0.0,
                'tax_ids': [],
                'tax_line_id': False,
                'currency_id': self.other_currency.id,
                'amount_currency': -220.0,
                'debit': 0.0,
                'credit': 110.01,
            },
        ],
        {
            'currency_id': self.other_currency.id,
            'fiscal_position_id': fiscal_position.id,
            'amount_untaxed': 183.33,
            'amount_tax': 36.67,
            'amount_total': 220.0,
        },
    )
    # ERP end

    uom_dozen = self.env.ref('uom.product_uom_dozen')
    with Form(invoice) as move_form:
        with move_form.invoice_line_ids.edit(0) as line_form:
            line_form.product_uom_id = uom_dozen

    # ERP start
    self.assertInvoiceValues(
        invoice,
        [
            {
                'product_id': product.id,
                'product_uom_id': uom_dozen.id,
                'price_unit': 2640.0,
                'price_subtotal': 2200.0,
                'price_total': 2640.0,
                'tax_ids': tax_price_include_2.ids,
                'tax_line_id': False,
                'currency_id': self.other_currency.id,
                'amount_currency': 2200.0,
                'debit': 1100.0,
                'credit': 0.0,
            },
            {
                'product_id': False,
                'product_uom_id': False,
                'price_unit': 0.0,
                'price_subtotal': 0.0,
                'price_total': 0.0,
                'tax_ids': [],
                'tax_line_id': tax_price_include_2.id,
                'currency_id': self.other_currency.id,
                'amount_currency': 440.0,
                'debit': 220.0,
                'credit': 0.0,
            },
            {
                'product_id': False,
                'product_uom_id': False,
                'price_unit': 0.0,
                'price_subtotal': 0.0,
                'price_total': 0.0,
                'tax_ids': [],
                'tax_line_id': False,
                'currency_id': self.other_currency.id,
                'amount_currency': -2640.0,
                'debit': 0.0,
                'credit': 1320.0,
            },
        ],
        {
            'currency_id': self.other_currency.id,
            'fiscal_position_id': fiscal_position.id,
            'amount_untaxed': 2200.0,
            'amount_tax': 440.0,
            'amount_total': 2640.0,
        },
    )
    # ERP end


TestAccountMoveInInvoiceOnchanges.test_in_invoice_line_onchange_product_2_with_fiscal_pos = test_in_invoice_line_onchange_product_2_with_fiscal_pos
TestAccountMoveInInvoiceOnchanges.test_in_invoice_line_onchange_product_2_with_fiscal_pos_2 = test_in_invoice_line_onchange_product_2_with_fiscal_pos_2
