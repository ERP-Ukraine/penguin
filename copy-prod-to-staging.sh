#!/bin/bash
PROD_DB="odoo15-penguin"
STAGING_DB="odoo15-penguin-staging"
PROD_VOL="/var/lib/docker/volumes/odoo15_penguin-odoo15-data/_data"
STAGE_VOL="/var/lib/docker/volumes/odoo15staging_penguin-odoo15staging-data/_data"

sudo rm -rf ${STAGE_VOL}/filestore/
sudo mkdir -p ${STAGE_VOL}/filestore/${STAGING_DB}
sudo chown -R 101:101 ${STAGE_VOL}/filestore
sudo cp -a ${PROD_VOL}/filestore/${PROD_DB}/. ${STAGE_VOL}/filestore/${STAGING_DB}/

sudo su - postgres -c "dropdb --if-exists ${STAGING_DB}"
sudo su - postgres -c "createdb ${STAGING_DB} --owner=odoo"
sudo su - postgres -c "pg_dump --no-owner ${PROD_DB} | psql ${STAGING_DB}"

UUID1=`python3 -c "import uuid; print(str(uuid.uuid1()))"`
UUID4=`python3 -c "import uuid; print(str(uuid.uuid4()))"`
CMD="UPDATE ir_cron set active = 'f';
DELETE FROM fetchmail_server;
DELETE FROM ir_mail_server;
UPDATE ir_config_parameter SET value = '$UUID4' WHERE key = 'database.secret';
UPDATE ir_config_parameter SET value = '$UUID1' WHERE key = 'database.uuid';"
sudo su - postgres -c "psql -d ${STAGING_DB}  -c \"$CMD\""
