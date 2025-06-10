from odoo.upgrade import util


def migrate(cr, version):

    to_uninstall = [
        'arnoldsports_multi_warehouse',
        'droggol_theme_common',
        'google_products_category_gcs',
        'google_shopping_feed_gcs',
        'payment_wallee',
        'sale_arnoldsports',
        'theme_penguin_default',
        'theme_prime',
        'website_cookiebot',
        'website_sale_coupon_penguin',
        'website_bloopark_detail',
        'website_penguin',

    ]

    for module in to_uninstall:
        if util.module_installed(cr, module):
            util.remove_module(cr, module)
