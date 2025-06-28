# -*- coding: utf-8 -*-
import requests, mimetypes
from odoo import fields, models, _
from odoo.exceptions import UserError


class ImportGoogleProductCategoriesWizard(models.TransientModel):
    _name = "import.google.product.categories.wizard"
    _description = "Import google product categories wizard"

    import_file_url = fields.Char("Import File URL", help="Please insert Google Category TXT File URL.", required=True)

    def import_google_categories(self):
        """
            This function call to Import Google Categories from URL.
            @author: GCS
            @return: True or Error
        """
        if not self.import_file_url:
            raise UserError(_("Opps!!! Not found Import File URL so please insert it and try again."))

        # Check File URL Type
        file_mimetype, file_encoding = mimetypes.guess_type(self.import_file_url)
        if file_mimetype != 'text/plain':
            raise UserError(_('Opps!!! Only TEXT(.txt) file are allowed so please select correct format.'))

        # Read File from URL
        try:
            resp_obj = requests.get(self.import_file_url, headers={}, timeout=20)
            resp_obj.raise_for_status()
            response = resp_obj.text
        except requests.HTTPError as e:
            error_msg = _("Something went wrong while Reading Category File using given File URL. \nError: %s" % (e))
            raise UserError(error_msg)
        except Exception as e:
            error_msg = _("Something went wrong while Reading Category File using given File URL. \nError: %s" % (e))
            raise UserError(error_msg)

        google_product_category_gcs_obj = self.env['google.product.category.gcs']
        for file_line in response.split("\n"):
            # Skip line which has comments
            if file_line[:1] == '#' or not file_line:
                continue

            category_code, category_full_path = file_line.split(' - ')
            category_hierarchy_list = category_full_path.split(' > ')
            vals = {
                'name': category_hierarchy_list[-1:][0],
                'category_code': category_code,
            }

            parent_category = None
            if len(category_hierarchy_list) > 1:
                parent_category = google_product_category_gcs_obj.search(
                    [('name', '=', category_hierarchy_list[-2:-1][0])], limit=1)
                vals['parent_categ_id'] = parent_category.id

            existing_google_category = google_product_category_gcs_obj.search([('category_code', '=', category_code)],
                                                                              limit=1)
            if not existing_google_category:
                google_product_category_gcs_obj.create(vals)
        return True
