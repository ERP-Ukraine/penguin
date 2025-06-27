#!/bin/bash

psql -c "UPDATE ir_module_module SET state='to upgrade' WHERE name='base';"

odoo -u all --upgrade-path=/usr/local/lib/python3.10/dist-packages/odoo/upgrade,/mnt/extra-addons/upgrades --stop-after-init
