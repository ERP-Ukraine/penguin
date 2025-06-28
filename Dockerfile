FROM erpukraine/odoo-ee-erpu:18.0-latest


USER root
RUN pip3 install --upgrade tnefparse
USER odoo
COPY --chown=odoo:odoo extra-addons/ /mnt/extra-addons
