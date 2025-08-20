/** @odoo-module **/

import PaymentForm from "@payment/js/payment_form";
import { _t } from "@web/core/l10n/translation";
import { rpc } from "@web/core/network/rpc";

PaymentForm.include({
    /**
     * Helper function to update the Wallee payment method.
     *
     * @private
     * @param {Object} wallee_method - The Wallee payment method details
     * @return {Promise} A promise that resolves with the result of the update
     */
    updateWalleeMethod(wallee_method) {
        const params = {
            'method_id': wallee_method.method_id,
            'space_id': wallee_method.space_id,
            'trans_id': wallee_method.trans_id,
            'trans_interface': wallee_method.trans_interface,
            'one_click_mode': wallee_method.one_click_mode,
        };

        return rpc("/payment/wallee/payment_method/update", params)
            .then(result => {
                return result;
            })
            .catch(error => {
                return { success: false, error: error.message || 'Unknown error' };
            });
    },

    /**
     * Override to handle Wallee payment flow.
     * This method is called before initiating the payment flow to perform
     * provider-specific pre-processing.
     *
     * @override
     */
    _initiatePaymentFlow(providerCode, paymentOptionId, paymentMethodCode, flow) {
        // Only handle Wallee payments, delegate others to the base implementation
        if (providerCode !== 'wallee') {
            return this._super(providerCode, paymentOptionId, paymentMethodCode, flow);
        }

        // Get the selected payment option
        const checkedRadio = this.el.querySelector(`input[name="o_payment_radio"]:checked`);
        if (!checkedRadio) {
            return this._super(providerCode, paymentOptionId, paymentMethodCode, flow);
        }

        // Extract Wallee-specific values from the dataset
        const dataset = checkedRadio.dataset;
        const wallee_method = {
            'trans_id': dataset.walleeTransId || '',
            'id': dataset.providerId || '',
            'method_id': dataset.walleeMethodCode || '',
            'space_id': dataset.walleeSpaceId || '',
            'trans_interface': dataset.walleeTrans_interface || '',
            'one_click_mode': dataset.walleeOne_click_mode || '',
        };

        paymentMethodCode = wallee_method.method_id;

        // Validate required fields
        if (!wallee_method.id || !wallee_method.space_id) {
            this._displayErrorDialog(
                _t('Configuration Error'),
                _t("Payment method configuration is incomplete. Please try a different payment method.")
            );
            return this._super(providerCode, paymentOptionId, paymentMethodCode, flow);
        }

        // Store reference to super method
        const _super = this._super.bind(this, providerCode, paymentOptionId, paymentMethodCode, flow);

        // Disable the button during processing
        this._disableButton(true);

        // Update Wallee payment method and proceed with payment flow
        return this.updateWalleeMethod(wallee_method)
            .then(result => {
                if (!result || !result.success) {
                    this._displayErrorDialog(
                        _t('Payment Error'),
                        _t("We couldn't update your payment method. Please try again.")
                    );
                    this._enableButton();
                    return Promise.reject(new Error('Payment update failed'));
                }

                // Call super to create transaction and get processing values
                return _super().then(() => {
                    // Transaction creation and processing values are handled by _super
                    // The redirect/lightbox handling is done in wallee_interface.js
                    return Promise.resolve();
                });
            })
            .catch(error => {
                this._displayErrorDialog(
                    _t('System Error'),
                    _t("A technical error occurred. Please contact support.")
                );
                this._enableButton();
                return Promise.reject(new Error('Payment processing error'));
            });
    }
});
