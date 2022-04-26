FROM erpukraine/custom:odoo-15.0ee-erpu-latest

COPY --chown=odoo:odoo extra-addons/ /mnt/extra-addons
