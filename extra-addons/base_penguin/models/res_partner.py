from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    external_id = fields.Integer('External ID', copy=False)
    country_ref = fields.Selection([
        ("collab_europe", "Collab Europe"),
        ("collab_swiss", "Collab Switzerland"),
        ("retail_shop_zurich", "Retail Shop Zurich"),
        ("retail_germany", "Retail Germany"),
        ("retail_austria", "Retail Austria"),
        ("retail_europe", "Retail Europe"),
        ("retail_swiss", "Retail Switzerland"),
        ("private_cust_swiss", "Private Customer Switzerland"),
        ("private_cust_europe", "Private Customer Europe"),
        ("online_cust_swiss", "Online Customer Switzerland"),
        ("online_cust_europe", "Online Customer Europe"),
        ("teamwear_swiss", "Teamwear Switzerland"),
        ("teamwear_europe", "Teamwear Europe"),
        ("ambassadors_agents", "Ambassadors + Agents"),
        ("j_S_swiss", "J+S Switzerland"),
        ("kalisti_test_buss", "Kalisti Textile Business"),
        ("benjamin_boss", "Benjamin Boss (Kalisti Europe)"),
        ("textile_buss", "Textile Business")
    ], "Customer Group")
    is_btwob_customer = fields.Boolean(string='B2B customer')
