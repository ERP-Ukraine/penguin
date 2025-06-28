from odoo import api, fields, models


class ProductProductSameImages(models.TransientModel):
    _name = 'product.product.same.images'
    _description = 'Copy images to same'

    product_id = fields.Many2one('product.product', 'Product', required=True)
    attribute_id = fields.Many2one('product.attribute', 'Attribute', required=True)

    @api.onchange('product_id')
    def _onchange_set_attribute_domain(self):
        res = {}

        if self.product_id:
            valid_attrs = self.product_id.mapped('product_template_attribute_value_ids.attribute_id')
            res['domain'] = {'attribute_id': [('id', 'in', valid_attrs.ids)]}

        return res

    def run(self):
        self.ensure_one()

        ptav = self.product_id.product_template_attribute_value_ids.filtered(lambda x: x.attribute_id == self.attribute_id)
        ptav.ensure_one()

        my_friends = ptav.ptav_product_variant_ids - self.product_id
        my_friends.write({'image_1920': self.product_id.image_1920})

        for friend in my_friends:
            domain = [('res_model', '=', 'product.image'),
                      ('res_field', '=', 'image_1920'),
                      ('res_id', 'in', friend.product_variant_image_ids.ids)]
            # search for all existing image attachments of my friend
            attachments = self.env['ir.attachment'].sudo().search(domain)
            existing_checksums = set(attachments.mapped('checksum'))

            for image in self.product_id.product_variant_image_ids:
                domain = [('res_model', '=', 'product.image'),
                          ('res_field', '=', 'image_1920'),
                          ('res_id', '=', image.id)]
                attach= self.env['ir.attachment'].sudo().search(domain, limit=1)
                if not attach:
                    continue

                # do not copy image if it is already there
                if attach.checksum in existing_checksums:
                    continue

                image_copy = image.copy()
                image_copy.write({'product_variant_id': friend.id})
