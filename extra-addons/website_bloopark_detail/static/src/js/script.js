(function ($) {
    "use strict";
    $(document).ready(function () {
        updateColorLabel();
        $('.js_variant_change[data-attribute_name="Color"]').each(function() {
            $(this).click(function() {
                updateColorLabel($(this).attr('data-value_name'));
            });
        });
        $("#add_to_cart_wrap").find('.js_check_product:first-child').remove();
    });

    function updateColorLabel(selectedColor) {
        const colorElement = $('li[data-attribute_name="Color"]').find('h6');
        let colorText = selectedColor || $('.custom-color-picker').find('.active span').text();

        colorElement.html(`Color <i class="fa fa-chevron-right"></i> <span class="color-label">${colorText}</span>`);
    }

})(jQuery);
