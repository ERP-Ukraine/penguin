import json
import logging
from odoo import http, api
from odoo.http import request

_logger = logging.getLogger(__name__)


class AuthApi(http.Controller):


    @http.route('/ffn/sso/oauth', auth='none', website=False, csrf=False, type='http', methods=['POST'])
    def get_countries(self, **kw):
        vals = []
        countries = request.env['res.country'].sudo().search([])
        lang = request.httprequest.accept_languages.best
        for country in countries:
            regions = []
            for state in country.state_ids:
                regions.append({
                    'region_id': state.id,
                    'region_name': state.name,
                    'region_code': state.code,
                })
            vals.append({
                "country_id": country.id,
                "country_name": country.name,
                "country_code": country.code,
                "country_regions": regions,
            })
        data = json.dumps({
            "status": 200,
            "message": "تم استرداد الدول بنجاح" if lang == 'ar' else "Countries Retrieved successfully",
            "response": {
                "countries": vals,
            }
        })
        headers = [('Content-Type', 'application/json')]
        return request.make_response(data, headers)

    def get_auth_failed_msg(self, lang):
        data = json.dumps({
            "status": 403,
            "message": "فشل عملية الدخول" if lang == 'ar' else "Authentication failed",
        })
        headers = [('Content-Type', 'application/json')]
        return request.make_response(data, headers, status=403)
