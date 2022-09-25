FROM erpukraine/custom:odoo-15.0ee-erpu-latest


USER root
RUN pip3 install --upgrade tnefparse
USER odoo
COPY --chown=odoo:odoo extra-addons/ /mnt/extra-addons
