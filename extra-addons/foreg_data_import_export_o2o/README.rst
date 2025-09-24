==================================
4EG Data Import/Export Odoo 2 Odoo
==================================

.. |badge1| image:: https://img.shields.io/badge/maturity-Beta-yellow.png
    :target: https://odoo-community.org/page/development-status
    :alt: Beta
.. |badge2| image:: https://img.shields.io/badge/license-PROPRIETARY-pink.png
    :target: https://4egrowth.de
    :alt: License: PROPRIETARY
.. |badge3| image:: https://img.shields.io/badge/odoo-17.0-blue.png
    :target: https://www.odoo.com/
    :alt: Odoo 17.0

|badge1| |badge2| |badge3|

This module extends the base import/export functionality to specifically handle one2one relationships between models, ensuring proper data integrity and relationship maintenance during import/export operations.

**Table of contents**

.. contents::
   :local:

Features
========

* **One2One Field Support**: Specialized handling of one2one relationships in data export and import.
* **Bidirectional Relationship Management**: Maintains both sides of one2one relationships during operations.
* **Relationship Integrity**: Ensures data consistency for one2one fields throughout the process.
* **XML ID Preservation**: Special handling to preserve XML IDs for one2one records.
* **Relationship Priority**: Configure import order for dependent one2one relationships.
* **Circular Reference Handling**: Handles circular references in one2one relationships.
* **Detailed Reports**: Enhanced summaries focused on one2one operations status.

Configuration
=============

To configure this module, you need to:

1. Go to *Data Import/Export → One2One Configuration*
2. Configure one2one relationships:

   * Define relationship priorities for proper import order
   * Configure which one2one fields should be included for each model
   * Set up default fields for one2one models

3. Advanced settings:

   * Configure bidirectional update behavior
   * Set validation rules for one2one relationships

Usage
=====

To use this module, you need to:

1. **Export Data with One2One Relationships**:

   * Navigate to *Data Import/Export* menu
   * Create a new record and provide a name
   * Select a model containing one2one relationships
   * Click "Export Data" button
   * The generated JSON file will include special handling for one2one fields

2. **Import Data with One2One Relationships**:

   * Navigate to *Data Import/Export* menu
   * Create a new record and provide a name
   * Upload your JSON file containing one2one relationships
   * Click "Import Data" button
   * The system will process one2one relationships according to configured priorities
   * Review the import summary showing the status of one2one fields

3. **Technical Options**:

   * Configure relationship handling for specific one2one fields
   * Set up validation rules for one2one data
   * Override default relationship priorities for special cases

Bug Tracker
===========

For bug reports and feature requests, please contact the 4E Growth support team.

Credits
=======

Authors
~~~~~~~

* 4E Growth GmbH

Contributors
~~~~~~~~~~~~

* 4E Growth Development Team <dev@4egrowth.de>

Maintainers
~~~~~~~~~~~

.. image:: https://4egrowth.de/web/image/website/1/logo
   :alt: 4E Growth GmbH
   :target: https://4egrowth.de

This module is maintained by 4E Growth GmbH.