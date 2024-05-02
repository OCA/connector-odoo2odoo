import logging

from odoo import fields, models

from odoo.addons.component.core import Component

_logger = logging.getLogger(__name__)


class OdooAccountAccount(models.Model):
    _name = "odoo.account.account"
    _inherit = "odoo.binding"
    _inherits = {"account.account": "odoo_id"}
    _description = "External Odoo Account Account"

    _sql_constraints = [
        (
            "external_id",
            "UNIQUE(external_id)",
            "External ID (external_id) must be unique!",
        ),
    ]

    def resync(self):
        if self.backend_id.main_record == "odoo":
            return self.with_delay().export_record(self.backend_id)
        else:
            return self.with_delay().import_record(
                self.backend_id, self.external_id, force=True
            )


class AccountAccount(models.Model):
    _inherit = "account.account"

    bind_ids = fields.One2many(
        comodel_name="odoo.account.account",
        inverse_name="odoo_id",
        string="Odoo Bindings",
    )


class AccountAccountAdapter(Component):
    _name = "odoo.account.account.adapter"
    _inherit = "odoo.adapter"
    _apply_on = "odoo.account.account"

    _odoo_model = "account.account"


class AccountAccountListener(Component):
    _name = "account.account.listener"
    _inherit = "base.connector.listener"
    _apply_on = ["account.account"]
    _usage = "event.listener"
