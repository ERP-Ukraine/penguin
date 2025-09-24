=====================
4EG Workflow O2O Sync
=====================

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

This module provides a flexible workflow engine for orchestrating API integrations and data synchronization between Odoo and external systems. It allows building complex integration workflows with conditional execution paths, webhooks, and custom Python scripts.

**Table of contents**

.. contents::
   :local:

Features
========

* **Configurable Workflows**: Create and manage integration workflows with multiple steps.
* **Flexible Execution Conditions**: Control job execution through sequence, dependencies, or custom Python logic.
* **Multiple Action Types**: 
  
  * Send API requests to external systems
  * Call webhooks
  * Execute Python scripts

* **Detailed Logging**: Track execution progress, duration, and status of each job.
* **Error Handling**: Configurable error handling strategies.
* **Scheduling**: Run workflows on demand or on schedule via cron jobs.

Configuration
=============

To configure this module, you need to:

1. Go to *Integration Dashboard → Workflow Configuration*
2. Create a new workflow and define its jobs
3. For each job, configure:

   **Execution conditions**: Define when the job should run
   **Action type**: Define what the job should do
   **Request configuration**: Set up API calls (if applicable)
   **Input and output handling**: Define data transformation

Usage
=====

To use this module, you need to:

1. **Create a Workflow**:

   * Define a clear name and description
   * Add jobs in the desired execution sequence

2. **Configure Jobs**:

   **Execution conditions** - Choose how the job is triggered:

   * Sequence Order: Run in predefined order
   * Job Done: Run when another job completes successfully
   * Job Failed: Run when another job fails
   * Python Script: Run when a custom condition is met

   **Action types** - Choose what the job does:

   * Send Request: Make API calls to external systems
   * Call Webhook: Send data to a webhook URL
   * Python Script: Execute custom Python code

3. **Run Workflows**:

   **Manual execution**: Trigger workflows from the interface
   **Automated execution**: Set up scheduled actions for automation

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
