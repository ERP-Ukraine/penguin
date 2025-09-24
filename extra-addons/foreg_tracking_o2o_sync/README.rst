================================
4EG Tracking O2O Synchronization
================================

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

This module enhances the 4EG Odoo-to-Odoo (O2O) synchronization system with comprehensive tracking and auditing capabilities. It provides detailed change tracking, chatter integration, and audit trails for all O2O operations to ensure transparency and accountability in data synchronization processes.

**Table of contents**

.. contents::
   :local:

Features
========

* **Automatic Tracking Setup**: Automatically configures tracking for important fields in O2O models.
* **Chatter Integration**: Enhanced chatter views showing tracking information for all O2O operations.
* **Audit Trail Management**: Comprehensive logging of changes in O2O instances, requests, and field configurations.
* **Multi-Model Support**: Tracking capabilities for:

  * O2O Instances
  * O2O Instance Fixed Values  
  * O2O Requests
  * O2O Request Fields

* **Tracking Mixin**: Reusable mixin class for easy tracking setup across different models.
* **Configuration Management**: Automated tracking field configuration with reset capabilities.
* **Detailed Logging**: Enhanced logging for tracking setup and configuration processes.
* **Change History**: Complete history of changes with timestamps and user information.

Technical Details
=================

**Dependencies**:
* ``foreg_o2o_sync``: Base O2O synchronization functionality
* ``tracking_manager``: OCA module providing enhanced tracking capabilities

**Models Extended**:
* ``foreg.o2o.instance``: O2O instance tracking
* ``foreg.o2o.instance.fixed.value``: Fixed value tracking  
* ``foreg.o2o.request``: Request tracking
* ``foreg.o2o.request.field``: Field mapping tracking

**Key Components**:
* ``ForegTrackingMixin``: Abstract model providing tracking setup methods
* Automatic tracking configuration via data files
* Enhanced chatter views for all tracked models

Configuration
=============

**Automatic Setup**:
The module automatically configures tracking during installation through data files. No manual configuration is required for basic functionality.

**Manual Configuration**:
For advanced users, tracking can be manually configured:

1. Access the tracking configuration through the model's setup methods
2. Use ``setup_tracking_fields()`` to enable tracking for specific models
3. Use ``reset_tracking_config()`` to reconfigure tracking settings

**Tracked Fields Configuration**:
Each model defines its own set of tracked fields through the ``get_tracking_fields()`` method, ensuring only relevant fields are monitored.

Usage
=====

**Viewing Tracking Information**:

1. Navigate to any O2O record (Instance, Request, or Field)
2. Check the chatter section to view change history
3. Review detailed logs of all modifications with timestamps and user information

**Managing Tracking Configuration**:

1. **Reset Tracking** (if needed):

   * Access the model through the developer mode
   * Call ``reset_tracking_config()`` method to reconfigure tracking

2. **Setup Custom Tracking**:

   * Override ``get_tracking_fields()`` in your custom models
   * Call ``setup_tracking_fields()`` to apply the configuration

**Monitoring Changes**:

* All changes to tracked fields are automatically logged
* Changes appear in the chatter with full context
* Historical data is preserved for audit purposes

Technical Implementation
========================

**Tracking Mixin**:
The ``ForegTrackingMixin`` provides a standardized way to implement tracking:

.. code-block:: python

    class MyModel(models.Model):
        _name = 'my.model'
        _inherit = ['my.model', 'foreg.tracking.mixin']
        
        def get_tracking_fields(self):
            return ['field1', 'field2', 'field3']

**Automatic Configuration**:
Tracking is automatically enabled during module installation through data files that call ``setup_tracking_fields()`` for each supported model.

**Configuration Parameters**:
The module uses configuration parameters to track setup status and prevent duplicate configurations.

Bug Tracker
===========

For bug reports and feature requests, please contact the 4E Growth support team.

Known Issues
============

* Tracking configuration is persistent and survives module upgrades
* Large numbers of tracked fields may impact performance on heavily modified records
* Some field types may require special handling for optimal tracking

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
