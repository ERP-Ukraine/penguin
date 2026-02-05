/** @odoo-module **/

import { WebsiteSale } from '@website_sale/js/website_sale';
import { _t } from "@web/core/l10n/translation";

WebsiteSale.include({
    
    onChangeVariant: function (ev) {
        this._super.apply(this, arguments);
        let $parent = $(ev.target).closest('.js_product');
        let title = $parent.find("[data-attribute_display_type='color']").find(".active").find("input")[0].dataset['value_name'];
        let elem = $parent.find("[data-attribute_display_type='color']").find(".attribute_name")[0].innerText;
        $parent.find("[data-attribute_display_type='color']").find(".attribute_name")[0].innerText = elem.split(' :')[0] + " : " + title;
    },

    _toggleDisable: function ($parent, isCombinationPossible) {
        if(isCombinationPossible){
            $parent.find(".css_not_available_msg")[0].style.display = "none"

        }else{
            $parent.find(".css_not_available_msg")[0].style.display = "block"
        }
    },
});
