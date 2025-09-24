======================
4EG Data Import/Export
======================

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

This module provides functionality to import and export data in JSON format, with support for handling relational fields (many2one, one2many, many2many) and maintaining XML IDs.

**Table of contents**

.. contents::
   :local:

Features
========

* **JSON Data Export**: Export data from any model to JSON format, including related records.
* **JSON Data Import**: Import data from JSON format to any model, creating or updating records.
* **Relational Field Handling**: Handle many2one, one2many, and many2many relationships.
* **XML ID Management**: Generate and maintain XML IDs during import/export operations.
* **Sensitive Data Control**: Optional export of sensitive information with security controls.
* **Summary Reports**: Detailed import/export summary showing processed records.
* **Batch Processing**: Efficient handling of large datasets with batch processing.
* **Archiving Support**: Option to include archived (inactive) records in exports.

Configuration
=============

To configure this module, you need to:

1. Go to *Data Import/Export → Configuration*
2. Set up the models and fields to export in System Parameters:

   * Use JSON format to define exportable models and fields
   * Configure which fields should be included for each model

3. Security settings:

   * Configure "Export Sensitive Information" setting to control sensitive data export
   * Set up access rights for users who should access import/export functionality

Usage
=====

To use this module, you need to:

1. **Export Data**:

   * Navigate to *Data Import/Export* menu
   * Create a new record and provide a name
   * Select the model to export from (or use context from another view)
   * Click "Export Data" button
   * Download the generated JSON file

2. **Import Data**:

   * Navigate to *Data Import/Export* menu
   * Create a new record and provide a name
   * Upload your JSON file
   * Click "Import Data" button
   * Review the import summary showing created and updated records

3. **Technical Options**:

   * Use context to export specific records
   * Configure field lists for precise control over exported data
   * Handle sensitive data with appropriate security settings

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
