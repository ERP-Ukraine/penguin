# -*- coding: utf-8 -*-
#################################################################################
# Author      : PIT Solutions AG. (<https://www.pitsolutions.com/>)
# Copyright(c): 2019 - Present PIT Solutions AG.
# License URL : https://www.webshopextension.com/en/licence-agreement/
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <https://www.webshopextension.com/en/licence-agreement/>
#################################################################################

"""
Constants used throughout the Wallee payment module.
This file centralizes all constant values to maintain consistency
and make updates easier across the module.
"""

# Transaction States
WALLEE_PENDING_STATES = [
    'CREATE',
    'PENDING',
    'CONFIRMED',
    'PROCESSING',
    'AUTHORIZED',
    'COMPLETED'
]

WALLEE_REFUND_PENDING_STATES = [
    'CREATE',
    'SCHEDULED',
    'MANUAL_CHECK'
]

# Transaction State Selections for UI
WALLEE_TRANSACTION_STATES = [
    ('AUTHORIZED', 'Authorized'),
    ('FULFILL', 'Fulfilled'),
    ('FAILED', 'Failed'),
    ('VOIDED', 'Voided'),
    ('PENDING', 'Pending'),
    ('SUCCESSFUL', 'Successful'),
    ('REFUNDED', 'Refunded'),
    ('DECLINE', 'Declined'),
]

# Interface Types for Payment Pages
WALLEE_INTERFACE_TYPES = [
    ('lightbox', 'Lightbox'),
    ('iframe', 'Iframe')
]

# Refund Types
WALLEE_REFUND_TYPES = [
    ('MERCHANT_INITIATED_ONLINE', 'Merchant ONLINE'),
]

# API Configuration
WALLEE_API_PROD_BASE_URL = "app-wallee.com"
WALLEE_API_TEST_BASE_URL = "app-wallee.com"

# Operation Types for API Calls
WALLEE_OPERATIONS = {
    'search_transaction': {
        'method': 'search'
    },
    'create_transaction': {
        'method': 'create'
    },
    'update_transaction': {
        'method': 'update'
    },
    'fetch_payment_methods': {
        'method': 'get'
    }
}
