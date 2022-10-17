odoo.define('website_sale_stock_penguin.VariantMixin', function(require) {
'use strict';

let publicWidget = require('web.public.widget');
let VariantMixin = require('website_sale_stock.VariantMixin');
const ajax = require('web.ajax');

VariantMixin._checkProductsAvailability = function (ptavId) {
   const productTemplateId = parseInt(document.querySelector('.product_template_id')?.value);
   if (!productTemplateId) { return };

   ajax.jsonRpc('/sale/get_all_published_combinations_website', 'call', {
       'product_template_id': productTemplateId,
       'product_template_attribute_value_id': ptavId,
   }).then((ptav_ids) => {
       document.querySelectorAll('.o_variant_pills').forEach(function (pill) {
           if (!(ptav_ids.includes(parseInt(pill.children[0].id)))) {
               pill.classList.remove('active');
               pill.classList.add('disabled');
               pill.disabled = true;
               pill.setAttribute('disabled', 'disabled');
           } else {
               pill.classList.remove('disabled');
               pill.disabled = false;
               pill.removeAttribute('disabled');
           };
       });
   });
};

VariantMixin._onClickColorAttributeLoadSize = function (ev, $parent, combination) {
    const colorPTAVId = parseInt(ev?.currentTarget?.querySelector('label.active')?.querySelector('input')?.dataset?.value_id);
    if (!colorPTAVId) { return };
    VariantMixin._checkProductsAvailability(colorPTAVId);
};

publicWidget.registry.WebsiteSale.include({
    /**
     * @override
     */
    _onChangeCombination: function () {
        this._super.apply(this, arguments);
        VariantMixin._onClickColorAttributeLoadSize.apply(this, arguments);
    },
});

return VariantMixin;

});
