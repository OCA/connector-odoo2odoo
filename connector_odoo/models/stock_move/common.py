# Copyright 2022 GreenIce, S.L. <https://greenice.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models

from odoo.addons.component.core import Component


class OdooStockMove(models.Model):
    _name = "odoo.stock.move"
    _inherit = "odoo.binding"
    _inherits = {"stock.move": "odoo_id"}
    _description = "External Odoo Stock Move"

    def resync(self):
        if self.backend_id.main_record == "odoo":
            return self.with_delay().export_record(self.backend_id)
        else:
            return self.with_delay().import_record(
                self.backend_id, self.external_id, force=True
            )

    def import_record(self, backend_id, external_id, force=False, picking_id=False):
        return super().import_record(
            backend_id.with_context(picking_id=picking_id), external_id, force=force
        )


class StockMoveAdapter(Component):
    _name = "odoo.stock.move.adapter"
    _inherit = "odoo.adapter"
    _apply_on = "odoo.stock.move"
    _odoo_model = "stock.move"


class StockMove(models.Model):
    _inherit = "stock.move"

    bind_ids = fields.One2many(
        comodel_name="odoo.stock.move",
        inverse_name="odoo_id",
        string="Odoo Bindings",
    )
