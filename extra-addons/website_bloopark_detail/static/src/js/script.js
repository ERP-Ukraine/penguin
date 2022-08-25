(function ($) {
    "use strict";
    $(document).ready(function () {
        $('li[data-attribute_name="Color"]').find('h6').html('Color <i class="fa fa-chevron-right"></i> <span class="color-label">' + $('.custom-color-picker').find('.active span').text() + '</span>');
        $('.js_variant_change').each(function() {
            $(this).click(function() {
                $('li[data-attribute_name="Color"]').find('h6').html('Color <i class="fa fa-chevron-right"></i> <span class="color-label">' + $(this).attr('data-value_name') + '</span>');
            });
        });
        alert('sdfsd');
    })
})(jQuery);

odoo.define('website_bloopark_detail.website', function (require) {
'use strict';
    const AccessoryProducts = document.querySelector('.tp-hook-accessory-products');
    AccessoryProducts.remove();
});
