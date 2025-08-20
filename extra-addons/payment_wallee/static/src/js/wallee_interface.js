/** @odoo-module **/

import publicWidget from '@web/legacy/js/public/public_widget';
import { _t } from "@web/core/l10n/translation";
import { renderToMarkup } from "@web/core/utils/render";
import { WalleeiFrameDialog } from "../js/iframe_dialog";

publicWidget.registry.PaymentForm.include({
    _processRedirectFlow: function (providerCode, paymentOptionId, paymentMethodCode, processingValues) {
        if (!processingValues) {
            return this._super(...arguments);
        }

        // Ensure we're using the payment method code from the parent class
        if (providerCode !== 'wallee') {
            return this._super(...arguments);
        }

        // Create form from processing values
        const div = document.createElement('div');
        div.innerHTML = processingValues['redirect_form_html'];
        this.redirectForm = div.querySelector('form');
        
        if (!this.redirectForm) {
            return;
        }

        // Configure form
        this.redirectForm.setAttribute('id', 'o_payment_redirect_form');
        this.redirectForm.setAttribute('target', '_top');
        document.body.appendChild(this.redirectForm);

        // Initialize interface based on transaction state
        const interfaceType = processingValues['wallee_tx_status'];
        const interfaceUrl = processingValues['wallee_tx_url'];
        const paymentMethod = processingValues['wallee_payment_method'] = paymentMethodCode;

        // Remove existing fields if they exist
        this.redirectForm.querySelectorAll('input[name="wallee_payment_method"], input[name="wallee_interface_type"], input[name="wallee_javascript_url"]').forEach(el => el.remove());

        // Add payment method to form data
        const paymentMethodInput = document.createElement('input');
        paymentMethodInput.type = 'hidden';
        paymentMethodInput.name = 'wallee_payment_method';
        paymentMethodInput.value = JSON.stringify(paymentMethod);
        this.redirectForm.appendChild(paymentMethodInput);

        // Add interface type to form data
        const interfaceTypeInput = document.createElement('input');
        interfaceTypeInput.type = 'hidden';
        interfaceTypeInput.name = 'wallee_interface_type';
        interfaceTypeInput.value = interfaceType;
        this.redirectForm.appendChild(interfaceTypeInput);

        // Add JavaScript URL to form data
        const scriptUrlInput = document.createElement('input');
        scriptUrlInput.type = 'hidden';
        scriptUrlInput.name = 'wallee_javascript_url';
        scriptUrlInput.value = interfaceUrl;
        this.redirectForm.appendChild(scriptUrlInput);

        switch (interfaceType) {
            case 'iframe':
                this.showWalleeInterface();
                break;
            case 'lightbox':
                this.showWalleeLightboxInterface(interfaceUrl, paymentMethod);
                break;
            default:
                this.redirectForm.submit();
        }
    },

    showWalleeInterface: function () {
        var self = this;

        // Get form data
        const formData = new FormData(this.redirectForm);
        const wallee_javascript_url = formData.get("wallee_javascript_url");
        let wallee_payment_method = formData.get("wallee_payment_method");

        // Parse payment method if needed
        try {
            if (wallee_payment_method) {
                wallee_payment_method = JSON.parse(wallee_payment_method);
            }
        } catch (e) {
            console.log('[Wallee] Failed to parse payment method');
        }

        if (!wallee_javascript_url || !wallee_payment_method) {
            console.log('[Wallee] Missing required data');
            return;
        }

        // Create dialog
        var content = renderToMarkup("wallee_interface.display_interface", {});
        self.dialog = this.call("dialog", "add", WalleeiFrameDialog, {
            body: content,
            confirm: () => {
                self.footerconfirmbtn = $('.btn-primary.btn-confirm');
                self.disableButton(self.footerconfirmbtn, true);
                self.footerclosebtn = $('.btn.btn-secondary.btn-close-modal');
                self.disableButton(self.footerclosebtn);
                if(self.walleehandler){
                    self.walleehandler.validate();
                }
            },
            cancel: () => {
                self.footerclosebtn = $('.btn-secondary.btn-close-modal');
                self.disableButton(self.footerclosebtn, true);
                self.footerconfirmbtn = $('.btn-primary.btn-confirm');
                self.disableButton(self.footerconfirmbtn);
                location.reload(true);
            },
        });

        // Load Wallee script and initialize handler
        $.getScript(wallee_javascript_url)
        .done(function(script, textStatus) {
            if (typeof window.IframeCheckoutHandler !== 'function') {
                $('ul.wallee-payment-errors').text("Payment interface failed to load");
                return;
            }

            try {
                self.walleehandler = new IframeCheckoutHandler(wallee_payment_method);
                
                // Wait for DOM to be ready
                $(document).ready(function() {
                    // Verify template is rendered
                    if (!$('#wallee-payment-form').length) {
                        throw new Error('Payment form element not found in DOM');
                    }
                    
                    self.walleehandler.create('wallee-payment-form');
                });

                // Set up validation callback
                self.walleehandler.setValidationCallback(function(validationResult) {
                    $('ul.wallee-payment-errors').html('');
                    if (validationResult.success) {
                        self.walleehandler.submit();
                    } else {
                        self.enableButton();
                        $.each(validationResult.errors, function(index, errorMessage) {
                            $('ul.wallee-payment-errors').append('<li>' + errorMessage + '</li>');
                        });
                    }
                });

                self.walleehandler.setHeightChangeCallback(function(height) {
                    // Handle height changes if needed
                });

                // Add initialization callback to handle iframe load
                self.walleehandler.setInitializeCallback(function() {
                    self.enableButton();
                });
            } catch (e) {
                $('ul.wallee-payment-errors').text("Failed to initialize payment form");
            }
        })
        .fail(function(jqxhr, settings, exception) {
            $('ul.wallee-payment-errors').text("Failed to load payment interface");
            
        });
        self._enableButton();
    },

    showWalleeLightboxInterface: function (wallee_lightbox_javascript_url, wallee_payment_method) {
        var self = this;
        
        if (!wallee_payment_method) {
            $('ul.wallee-payment-errors').append('<li>Invalid payment method configuration</li>');
            return;
        }
        
        $.getScript(wallee_lightbox_javascript_url)
            .done(function(script, textStatus) {
                if (!window.LightboxCheckoutHandler || !window.LightboxCheckoutHandler.startPayment) {
                    $('ul.wallee-payment-errors').append('<li>Payment interface initialization failed. Please try again.</li>');
                    return;
                }

                try {
                    self.walleehandler = window.LightboxCheckoutHandler.startPayment(wallee_payment_method, function(validationResult) {
                        $('ul.wallee-payment-errors').html('');
                        if (validationResult.success) {
                            self.walleehandler.submit();
                        } else {
                            $.each(validationResult.errors, function(index, errorMessage) {
                                $('ul.wallee-payment-errors').append('<li>' + errorMessage + '</li>');
                            });
                        }
                    });
                } catch (e) {
                    $('ul.wallee-payment-errors').append('<li>Failed to initialize payment interface. Please try again.</li>');
                }
            })
            .fail(function(jqxhr, settings, exception) {
                $('ul.wallee-payment-errors').append('<li>Failed to load payment interface. Please try again.</li>');
            });
    },

    init: function (parent, wallee_payment_method) {
        this._super.apply(this, arguments);
        this._wallee_payment_method = wallee_payment_method;
    },

    disableButton: function ($button, loader) {
        loader = loader || undefined;
        $button.attr('disabled', true);
        if (loader){
            $button.children('.fa-lock').removeClass('fa-lock');
            $button.prepend('<span class="o_loader"><i class="fa fa-refresh fa-spin"></i>&nbsp;</span>');
        }
    },

    enableButton: function () {
        var buttons = [$("#iframe_confirm"), $("#iframe_cancel")];
        buttons.forEach(function(button) {
            button.attr('disabled', false);
            button.children('.fa').addClass('fa-lock');
            button.find('span.o_loader').remove();
        });
        
        // Ensure UI is unblocked using Odoo's UI service
        this.call('ui', 'unblock');
    },
});
