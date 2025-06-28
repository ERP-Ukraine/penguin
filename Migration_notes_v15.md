# pre-upgrade

## PSQL

Frontend Layout view has duplicate because it was edited manually.
Some views are inheriting that view.

We need to reassign child views to original view.

```postgresql
update ir_ui_view set active = 'f' where id = 2017;
```

## Odoo shell

uninstall modules

```python
modules = ["payment_wallee",]
self.env["ir.module.module"].search([("name", "in", modules)]).button_immediate_uninstall()
self.env.cr.commit()
```

## Post upgrade

```postgresql
update ir_ui_view set inherit_id = 192 where inherit_id = 2017;
update ir_ui_view set active = 'f' where id = 2017;
update ir_ui_view set active = 't' where id = 192;
```
