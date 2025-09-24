###############################################################################
#
#    Copyright (C) 2024-TODAY 4E Growth GmbH (<https://4egrowth.de>)
#    All Rights Reserved.
#
#    This software is proprietary and confidential. Unauthorized copying,
#    modification, distribution, or use of this software, via any medium,
#    is strictly prohibited without the express written permission of
#    4E Growth GmbH.
#
#    This software is provided under a license agreement and may be used
#    only in accordance with the terms of said agreement.
#
###############################################################################

from odoo import models


class ForegO2oInstance(models.Model):
    _name = "foreg.o2o.instance"
    _inherit = [
        "foreg.o2o.instance",
        "mail.thread",
        "mail.activity.mixin",
        "foreg.tracking.mixin",
    ]

    def get_tracking_fields(self):
        """Get list of O2O instance fields to be tracked for changes.

        Returns a comprehensive list of fields that should be monitored for
        changes in the O2O instance configuration. This includes connection
        settings, import/export flags, date ranges, relationships, and other
        critical configuration fields that affect synchronization behavior.

        Returns:
            list: List of field names to be tracked for changes in the chatter

        Example:
            >>> tracking_fields = self.get_tracking_fields()
            >>> print(len(tracking_fields))
            23
        """
        tracking_fields = [
            "host",  # Connection endpoint changes
            "is_import_product",  # Product import setting changes
            "is_export_product",  # Product export setting changes
            "is_import_order",  # Order import setting changes
            "is_import_attributes",  # Attributes import setting changes
            "is_update_product",  # Product update setting changes
            "is_upload_product_img",  # Product image export setting changes
            "is_import_product_img",  # Product image import setting changes
            "is_import_price_items",  # Price items import setting changes
            "is_import_property",  # Properties import setting changes
            "is_import_product_brand",  # Product brand import setting changes
            "is_import_template",  # Template import setting changes
            "is_import_catalogs",  # Catalogs import setting changes
            "orders_from_date",  # Order import date range changes
            "orders_to_date",  # Order import date range changes
            "order_prefix",  # Order prefix filter changes
            "payment_term_id",  # Payment term setting changes
            "sales_team_id",  # Sales team setting changes
            "account_receiveable_id",  # Account receivable setting changes
            "pricelist_id",  # Pricelist setting changes
            "warehouse_id",  # Warehouse setting changes
            # Many2many and One2many fields
            "product_tmpl_ids",  # Product templates relationship changes
            "location_ids",  # Stock locations relationship changes
            "fixed_value_ids",  # Fixed values relationship changes
        ]
        return tracking_fields
