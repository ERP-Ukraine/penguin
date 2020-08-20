odoo.define('website_sale_penguin.website_sale', function (require) {
    'use strict';

    var publicWidget = require('web.public.widget');
    var core = require('web.core');

    publicWidget.registry.categoryGroup = publicWidget.Widget.extend({
        selector: '.oe_category_group',
        events: {
            'click .oe_category_move_left': '_onClickLeftArrow',
            'click .oe_category_move_right': '_onClickRightArrow'
        },
        init: function () {
            this._super.apply(this, arguments);
        },
        start: function () {
            var def = this._super.apply(this, arguments);

            this.categoryGroup = this.$('.category-group');
            this.rightArrow = this.$('.oe_category_move_left');
            this.leftArrow = this.$('.oe_category_move_right');

            this._scrollToLink();
            this._horizontalScroll();

            core.bus.on('resize', this, _.debounce(this._onResize, 250));
            this.categoryGroup.on('scroll', _.throttle(this._horizontalScroll.bind(this), 200));

            return def;
        },
        _scrollToLink: function () {
            var activeLink = this.$('a.active')[0];
            if (activeLink) {
                activeLink.scrollIntoView(false);
            }
        },
        _horizontalScroll: function () {
            var categEl = this.categoryGroup[0];

            if (categEl.offsetWidth === categEl.scrollWidth) {
                this.rightArrow.removeClass('show');
                this.leftArrow.removeClass('show');
            } else {
                if (categEl.scrollLeft < 5) {
                    this.rightArrow.removeClass('show');
                } else {
                    this.rightArrow.addClass('show');
                }

                var offsetRight = Math.abs(categEl.scrollWidth - categEl.scrollLeft - categEl.offsetWidth);
                if (offsetRight < 5) {
                    this.leftArrow.removeClass('show');
                } else {
                    this.leftArrow.addClass('show');
                }
            }
        },
        _onClickLeftArrow: function () {
            var offsetWidth = this.categoryGroup[0].offsetWidth;
            this.categoryGroup.animate({scrollLeft: '-=' + offsetWidth}, 250);
        },
        _onClickRightArrow: function () {
            var offsetWidth = this.categoryGroup[0].offsetWidth;
            this.categoryGroup.animate({scrollLeft: '+=' + offsetWidth}, 250);
        },
        _onResize: function () {
            this._horizontalScroll();
        }
    })
})