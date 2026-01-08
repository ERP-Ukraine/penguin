{
    "name": "Penguin : Variants Management",
    "author": "Odoo PS",
    "version": "18.0.0.0.3",
    "website": "https://www.odoo.com",
    "depends": ["website_event", "website_sale"],
    "data": [
        # Backend
        'views/backend/event_event_views.xml',
        # Frontend
        "views/event_templates_page_registration.xml",
    ],
    'assets': {
        'web.assets_frontend': [
            # SCSS
            'website_penguin_odoo/static/src/scss/layout/product.scss',
            # Global QWeb JS Templates
            'website_penguin_odoo/static/src/js/product_variant.js',
        ],
    },
}
