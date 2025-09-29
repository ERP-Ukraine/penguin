{
    "name": "Penguin : Variants Management",
    "author": "Odoo PS",
    "version": "18.0.0.0.0",
    "website": "https://www.odoo.com",
    "depends": ["stock", "website_event", "website_sale"],
    "data": [
        # Backend
        'views/backend/event_event_views.xml',
        # Frontend
        "views/event_templates_page_registration.xml",
    ],
    'assets': {
        'web.assets_frontend': [
            'website_penguin/static/src/js/product_variant.js',
        ],
    },
}
