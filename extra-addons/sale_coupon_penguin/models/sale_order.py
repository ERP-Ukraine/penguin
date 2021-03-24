# -*- coding: utf-8 -*-
from odoo import models, _
from odoo.tools import safe_eval


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _create_reward_coupon(self, program):
        # before creating new coupon we check if coupon already exists
        # and has been reserved for current order and program
        coupon = self.env['sale.coupon'].search([
            ('program_id', '=', program.id),
            ('state', 'in', ('reserved', 'expired')),
            ('partner_id', '=', self.partner_id.id),
            ('order_id', '=', self.id),
            ('discount_line_product_id', '=', program.discount_line_product_id.id),
        ], limit=1)
        if coupon:
            discount_products = self.env['product.product'].search(safe_eval(program.rule_id.rule_products_domain))
            if program.reward_type == 'penguin_promocode_amount':
                discount_amount = sum(self.order_line.filtered(
                    lambda l: l.product_id in discount_products).mapped('price_subtotal'))
                if discount_amount:
                    coupon.write({'discount_amount': discount_amount})
            return coupon
        return super(SaleOrder, self)._create_reward_coupon(program)


    def _get_reward_values_discount(self, program):
        if program.reward_type == 'penguin_promocode_amount':
            taxes = program.discount_line_product_id.taxes_id
            if self.fiscal_position_id:
                taxes = self.fiscal_position_id.map_tax(taxes)
            coupon = self.applied_coupon_ids.filtered(lambda coupon: coupon.program_id == program)
            return [{
                'name': _("Discount: ") + program.name,
                'product_id': program.discount_line_product_id.id,
                'price_unit': - coupon.currency_id.compute(coupon.discount_amount, self.currency_id),
                'product_uom_qty': 1.0,
                'product_uom': program.discount_line_product_id.uom_id.id,
                'is_reward_line': True,
                'tax_id': [(4, tax.id, False) for tax in taxes],
            }]
        else:
            return super()._get_reward_values_discount(program)

    def _get_reward_line_values(self, program):
        # add new program reward type case
        self.ensure_one()
        self = self.with_context(lang=self.partner_id.lang)
        program = program.with_context(lang=self.partner_id.lang)
        if program.reward_type == 'penguin_promocode_amount':
            return self._get_reward_values_discount(program)
        else:
            return super()._get_reward_line_values(program)

    def _send_reward_coupon_mail(self):
        # override method for posting message in sale order
        template = self.env.ref('sale_coupon.mail_template_sale_coupon', raise_if_not_found=False)
        if template:
            for order in self:
                for coupon in order.generated_coupon_ids:
                    order.message_post_with_template(
                        template.id, composition_mode='comment',
                        model='sale.coupon', res_id=coupon.id,
                        email_layout_xmlid='mail.mail_notification_light',
                    )
                # -- custom code --
                msg = 'Coupon <a href=# data-oe-model=sale.coupon data-oe-id=%d>%s</a> ' \
                      'sent to <a href=# data-oe-model=res.partner data-oe-id=%d>%s</a>'
                order.message_post(body=_(
                    msg % (coupon.id, coupon.code, order.partner_id.id, order.partner_id.name)))
