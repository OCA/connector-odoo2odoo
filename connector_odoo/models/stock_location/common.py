# Copyright 2022 Greenice, S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import logging

from odoo import fields, models

from odoo.addons.component.core import Component

_logger = logging.getLogger(__name__)


class OdooStockLocation(models.Model):
    _name = "odoo.stock.location"
    _inherit = [
        "odoo.binding",
    ]
    _inherits = {"stock.location": "odoo_id"}
    _description = "Odoo Location"

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


class StockLocation(models.Model):
    _inherit = "stock.location"

    bind_ids = fields.One2many(
        comodel_name="odoo.stock.location",
        inverse_name="odoo_id",
        string="Odoo Bindings",
    )


class StockLocationAdapter(Component):
    _name = "odoo.stock.location.adapter"
    _inherit = "odoo.adapter"
    _apply_on = "odoo.stock.location"
    _odoo_model = "stock.location"
