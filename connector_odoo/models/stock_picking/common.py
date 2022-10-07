# Copyright 2022 Greenice, S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import logging

from odoo import fields, models

from odoo.addons.component.core import Component

_logger = logging.getLogger(__name__)


class OdooStockPicking(models.Model):
    _name = "odoo.stock.picking"
    _inherit = [
        "odoo.binding",
    ]
    _inherits = {"stock.picking": "odoo_id"}
    _description = "Odoo Picking"

    _sql_constraints = [
        (
            "external_id",
            "UNIQUE(external_id)",
            "External ID (external_id) must be unique!",
        ),
    ]

    def _compute_import_state(self):
        for move_id in self:
            waiting = len(
                move_id.queue_job_ids.filtered(
                    lambda j: j.state in ("pending", "enqueued", "started")
                )
            )
            error = len(move_id.queue_job_ids.filtered(lambda j: j.state == "failed"))
            if waiting:
                move_id.import_state = "waiting"
            elif error:
                move_id.import_state = "error_sync"
            else:
                move_id.import_state = "done"

    import_state = fields.Selection(
        [
            ("waiting", "Waiting"),
            ("error_sync", "Sync Error"),
            ("done", "Done"),
        ],
        default="waiting",
        compute=_compute_import_state,
    )

    def resync(self):
        if self.backend_id.read_operation_from == "odoo":
            raise NotImplementedError
        else:
            return self.with_delay().import_record(
                self.backend_id, self.external_id, force=True
            )

    def set_destination_pending_pickings(
        self,
    ):
        pass


class StockPicking(models.Model):
    _inherit = "stock.picking"

    bind_ids = fields.One2many(
        comodel_name="odoo.stock.picking",
        inverse_name="odoo_id",
        string="Odoo Bindings",
    )

    queue_job_ids = fields.Many2many(
        comodel_name="queue.job",
    )


class StockPickingAdapter(Component):
    _name = "odoo.stock.picking.adapter"
    _inherit = "odoo.adapter"
    _apply_on = "odoo.stock.picking"
    _odoo_model = "stock.picking"
