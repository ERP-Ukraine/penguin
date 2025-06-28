# -*- coding: utf-8 -*-
#!/usr/bin/python3
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import json, logging
from werkzeug.utils import redirect
import werkzeug.urls
import werkzeug.utils
import werkzeug.wrappers

from odoo import http, registry
from odoo.http import request
from odoo.addons.portal.controllers.web import Home

logger = logging.getLogger(__name__)

class GoogleShoppingAuth2(http.Controller):

    @http.route(['/google_account/authentication2'], type='http', auth="none")
    def oauth2callback(self, **kw):
        """ 
            This route/function is called by Google when user Accept/Refuse the consent/auth of Google.
            return: Redirect Success URL / Error URL
        """
        state = json.loads(kw['state'])
        database_name = state.get('database')
        base_url_return = state.get('base_url')
        gs_account = state.get('gs_account')

        if kw.get('code'):
            request.env['google.shopping.feed.account'].set_authorize_gs_code(gs_account, kw['code'])
            return redirect(base_url_return)
        elif kw.get('error'):
            return redirect("%s%s%s" % (base_url_return, "?error=", kw['error']))
        else:
            return redirect("%s%s" % (base_url_return, "?error=Unknown_error"))
      
class Website(Home):      
            
    @http.route(['/google<string(length=16):key>.html'], type='http', auth="public", website=True, sitemap=False)
    def google_console_search(self, key, **kwargs):
        searched_file_name = "google%s.html" % key
        gsf_account = request.env['google.shopping.feed.account'].sudo().search([('google_shopping_account_claim_filename', '=', searched_file_name)], limit=1)
        
        if not request.website.google_search_console and not gsf_account:
            logger.warning('Google Search Console not enable')
            raise werkzeug.exceptions.NotFound()
        
        if gsf_account:
            trusted = gsf_account.google_shopping_account_claim_filename.lstrip('google').rstrip('.html')
            if key != trusted:
                if key.startswith(trusted):
                    gsf_account.sudo().google_shopping_account_claim_filename = "google%s.html" % key
                else:
                    logger.warning('Google Search Console %s not recognize' % key)
                    raise werkzeug.exceptions.NotFound()
            return request.make_response("google-site-verification: %s" % gsf_account.google_shopping_account_claim_filename)
        else:
            trusted = request.website.google_search_console.lstrip('google').rstrip('.html')
            if key != trusted:
                if key.startswith(trusted):
                    request.website.sudo().google_search_console = "google%s.html" % key
                else:
                    logger.warning('Google Search Console %s not recognize' % key)
                    raise werkzeug.exceptions.NotFound()
            return request.make_response("google-site-verification: %s" % request.website.google_search_console)

        