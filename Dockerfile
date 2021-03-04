FROM erpukraine/custom:odoo-13.0ee-erpu-20210303

COPY --chown=odoo:odoo extra-addons/ /mnt/extra-addons
