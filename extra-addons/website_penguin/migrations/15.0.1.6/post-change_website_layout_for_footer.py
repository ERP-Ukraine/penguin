# -*- coding: utf-8 -*-
import logging
from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    footer_refs = ['website.footer_custom', 'website.template_footer_descriptive',
                   'website.template_footer_centered', 'website.template_footer_links',
                   'website.template_footer_minimalist', 'website.template_footer_contact']

    footer_templates = env['ir.ui.view'].search([('key', 'in', footer_refs)])
    copied_footer_templates = footer_templates.filtered(lambda v: v.xml_id == '')
    _logger.info('Disabling %d copied footer views', len(copied_footer_templates))
    copied_footer_templates.active = False

    website_layouts = env['ir.ui.view'].search([('key', '=', 'website.layout')])
    website_layout = website_layouts.filtered(lambda v: v.xml_id == '')
    if not website_layout:
        return
    penguin_footer = env.ref('website_penguin.penguin_footer', raise_if_not_found=False)
    if not penguin_footer:
        return
    _logger.info('Enabling penguin footer for website.layout with id %d', website_layout.id)
    penguin_footer.inherit_id = website_layout.id

