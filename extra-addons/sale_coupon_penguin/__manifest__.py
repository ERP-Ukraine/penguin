# -*- coding: utf-8 -*-
{
    "name": "Penguin Coupons",
    "summary": "Sales Coupon Customs Design",
    "author": "ERP Ukraine",
    "website": "https://erp.co.ua",
    "support": "support@erp.co.ua",
    "license": "LGPL-3",
    "category": "Sales/Sales",
    "version": "1.3.1",
    "depends": ["loyalty"],
    "data": [
        "report/loyalty_report_templates.xml",
        "report/loyalty_report.xml",
    ],
    "assets": {
        "web.report_assets_common": [
            "/sale_coupon_penguin/static/src/scss/pengin_coupon_report.scss",
        ]
    },
    "installable": True,
    "auto_install": True,
    "application": False,
}
