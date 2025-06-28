from odoo.upgrade import util


def migrate(cr, version):
    util.delete_unused(cr, 'payment_wallee.redirect_form', deactivate=True)
    util.remove_asset(cr, 'web.assets_frontend')
    util.remove_asset(cr, 'web.assets_qweb')

    # remove IMP refs to keep records while uninstalling payment_wallee.
    # make fk constaints of payment method line and payment transaction happy
    cr.execute("DELETE FROM ir_model_data WHERE module='payment_wallee' AND name='payment_method_wallee'")
    cr.execute("DELETE FROM ir_model_data WHERE module='payment_wallee' AND name='payment_acquirer_walleee'")
    cr.execute("DELETE FROM ir_model_data WHERE module='payment_wallee' AND name='payment_acquirer_wallee'")
    cr.execute("DELETE FROM ir_model_data WHERE module='payment_wallee' AND name='redirect_form'")

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
        'website_sale_google_recaptcha',
        'website_gtm',
        'penguin_favicon',
        'website_form_google_recaptcha',

    ]

    for module in to_uninstall:
        if util.module_installed(cr, module):
            util.remove_module(cr, module)
