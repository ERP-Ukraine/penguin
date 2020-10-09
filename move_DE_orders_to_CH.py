# odoo shell
eur_pl_id = 2
ewh_id = 3
germany = 57
kalisti_europe = 2
fpos_b2c_2020 = 9
fpos_b2b_not_2020 = 11
fpos_b2b = 10
orders = self.env['sale.order'].search(
    [('company_id', '=', kalisti_europe), ('state', '=', 'done')])
for i, order in enumerate(orders, 1):
    print(i)
    order.action_unlock()
    fpos_id = fpos_b2c_2020
    if (not order.partner_id.country_id or order.partner_id.country_id.id == germany):
        fpos_id = fpos_b2b_not_2020 if order.date_order.year != 2020 else fpos_b2c_2020
    else:
        # DE export to AT
        fpos_id = fpos_b2b
    order.write(
        dict(
            company_id=1,
            pricelist_id=eur_pl_id,
            warehouse_id=ewh_id,
            fiscal_position_id=fpos_id))
    order._compute_tax_id()
    order.action_done()

orders = self.env['sale.order'].search([('company_id', '=', 1), ('state', '=', 'future_sale')])
for line in orders.mapped('order_line'):
    if not line.product_id.active:
        code = line.product_id.default_code
        if not code:
            continue
        prod = self.env['product.product'].search([('default_code', '=', code), ('active', '=', True)], limit=1)
        if prod:
            line.write(dict(product_id=prod.id))

names = set()
for line in orders.mapped('order_line'):
    if not line.product_id.active:
        names.add(line.order_id.name)

names = set()
for line in orders.mapped('order_line'):
    if not line.product_id.active:
        print(line.product_id.default_code)
        names.add(line.order_id.name)
