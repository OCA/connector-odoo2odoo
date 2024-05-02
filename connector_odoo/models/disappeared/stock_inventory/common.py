# Copyright 2022 Greenice, S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)
from odoo import fields, models

from odoo.addons.component.core import Component


class OdooStockInventory(models.Model):
    _name = "odoo.stock.inventory.disappeared"
    _inherit = "odoo.binding"
    _inherits = {"stock.picking": "odoo_id"}

    _sql_constraints = [
        (
            "external_id",
            "UNIQUE(external_id)",
            "External ID (external_id) must be unique!",
        ),
    ]

    odoo_id = fields.Many2one(
        comodel_name="stock.picking", string="Picking", ondelete="cascade"
    )
    backend_state = fields.Char()

    def resync(self):
        if self.backend_id.main_record == "odoo":
            raise NotImplementedError
        else:
            return self.with_delay().import_record(
                self.backend_id,
                self.external_id,
                force=True,
            )

    def _set_inventory_state(self):
        if self.backend_state == self.odoo_id.state:
            return

        if self.backend_state == "done":
            for move_id in self.move_lines:
                move_id.quantity_done = move_id.product_uom_qty
            self.odoo_id.button_validate()
        elif self.backend_state == "cancel":
            self.odoo_id.action_cancel()
        elif self.backend_state == "confirmed":
            self.odoo_id.action_confirm()


class StockInventoryDissapearedAdapter(Component):
    _name = "odoo.stock.inventory.dissapeared.adapter"
    _inherit = "odoo.adapter"
    _apply_on = "odoo.stock.inventory.disappeared"

    _odoo_model = "stock.picking"


class StockPicking(models.Model):
    _inherit = "stock.picking"

    bind_stock_inventory_dissapeared_ids = fields.One2many(
        comodel_name="odoo.stock.inventory.disappeared",
        inverse_name="odoo_id",
        string="Odoo Stock Inventory (Disappeared) Bindings",
    )
