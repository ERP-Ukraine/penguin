
(function ($) {
    "use strict";
    $(document).ready(function () {
        $('li[data-attribute_name="Color"]').find('h6').html('Color <i class="fa fa-chevron-right"></i> <span class="color-label">' + $('.custom-color-picker').find('.active span').text() + '</span>');
        $('.js_variant_change').each(function() {
            $(this).click(function() {
                $('li[data-attribute_name="Color"]').find('h6').html('Color <i class="fa fa-chevron-right"></i> <span class="color-label">' + $(this).attr('data-value_name') + '</span>');
            });
        });
        $(".size-guide").insertBefore(".css_quantity");
        $("#add_to_cart_wrap").find('.js_check_product:first-child').remove();
    })
})(jQuery);