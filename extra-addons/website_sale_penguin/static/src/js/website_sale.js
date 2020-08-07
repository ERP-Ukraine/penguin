odoo.define('website_sale_penguin.website_sale', function (require) {
    'use strict';

    require('web.dom_ready');

    // scroll selected category to view
    $('.category-group a.active').toArray().forEach(function (link) {
        link.scrollIntoView(false);
    })
})