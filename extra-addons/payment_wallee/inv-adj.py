
import json
from collections import defaultdict

a = """138.5.5 1
138.5.3 5
138.5.2 5
138.5.1 5
138.5.4 3"""

l = a.split('\n')
ll = [e.split(' ') for e in l]
d = defaultdict(int)

for e in ll:
    if len(e) != 2:
        continue
    k, v = e
    if v:
        d[k] += int(v)

print(json.dumps(d))

#####

i = self.env['stock.inventory'].browse(11)


il = i.line_ids

for line in il:
    article = line.product_id.default_code
    if article in d:
        line.product_qty = d[article]
        d.pop(article)


l = il[0]


done = {}

for k, v in d.items():
    product = self.env['product.product'].search([('default_code', '=', k)], limit=1)
    if not product:
        continue
    self.env['stock.inventory.line'].create({
        'product_id': product.id,
        'product_uom_id': l.product_uom_id.id,
        'location_id': l.location_id.id,
        'product_qty': v,
        'inventory_id': l.inventory_id.id,
    })
    done[k] = v
