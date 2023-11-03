# Copyright 2022 Greenice, S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import fields, models

from odoo.addons.component.core import Component


class OdooResCurrency(models.Model):
    _name = "odoo.res.currency"
    _inherit = [
        "odoo.binding",
    ]
    _inherits = {"res.currency": "odoo_id"}
    _description = "Odoo Currency"

    _sql_constraints = [
        (
            "external_id",
            "UNIQUE(external_id)",
            "External ID (external_id) must be unique!",
        ),
    ]

    def resync(self):
        if self.backend_id.main_record == "odoo":
            raise NotImplementedError
        else:
            return self.with_delay().import_record(
                self.backend_id, self.external_id, force=True
            )


class ResCurrency(models.Model):
    _inherit = "res.currency"

    bind_ids = fields.One2many(
        comodel_name="odoo.res.currency",
        inverse_name="odoo_id",
        string="Odoo Bindings",
    )


class ResCurrencyAdapter(Component):
    _name = "odoo.res.currency.adapter"
    _inherit = "odoo.adapter"
    _apply_on = "odoo.res.currency"
    _odoo_model = "res.currency"
