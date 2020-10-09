from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    external_id = fields.Integer('External ID', copy=False)
    washing_instruction_id = fields.Many2one('product.washing.instruction', string='Washing Instruction')
    material_id = fields.Many2one('product.material', string='Material')
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female')
    ], string='Gender')
    size_ids = fields.Many2many('product.size', string='Size')
    feature_ids = fields.Many2many('product.feature', string='Features')


class ProductProduct(models.Model):
    _inherit = 'product.product'

    external_id = fields.Integer('Integer ID', copy=False)


class ProductCategory(models.Model):
    _inherit = 'product.category'

    external_id = fields.Integer('Integer ID', copy=False)


class ProductWashingInstruction(models.Model):
    _name = 'product.washing.instruction'
    _description = 'Product Washing Instruction'

    external_id = fields.Integer('External ID', copy=False)
    name = fields.Char('Name', translate=True)
    description = fields.Text('Description', translate=True)


class ProductMaterial(models.Model):
    _name = 'product.material'
    _description = 'Product Material'

    external_id = fields.Integer('External ID', copy=False)
    name = fields.Char('Name', translate=True)
    description = fields.Text('Description', translate=True)


class ProductSize(models.Model):
    _name = 'product.size'
    _description = 'Product Size'

    external_id = fields.Integer('External ID', copy=False)
    name = fields.Char('Name', copy=False, translate=True)
    sequence = fields.Integer('Sequence')
    small = fields.Float('Small', digits=(16, 2), default=0.0)
    medium = fields.Float('Medium', digits=(16, 2), default=0.0)
    large = fields.Float('Large', digits=(16, 2), default=0.0)
    x_small = fields.Float('X-Small', digits=(16, 2), default=0.0)
    x_large = fields.Float('X-Large', digits=(16, 2), default=0.0)
    xx_large = fields.Float('2X-Large', digits=(16, 2), default=0.0)
    xxx_large = fields.Float('3X-Large', digits=(16, 2), default=0.0)


class ProductFeature(models.Model):
    _name = 'product.feature'
    _description = 'Product Feature'

    external_id = fields.Integer('External ID', copy=False)
    name = fields.Char('Name', translate=True)
