import logging

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping

_logger = logging.getLogger(__name__)


class StockMoveBatchImporter(Component):
    """Import Stock moves."""

    _name = "odoo.stock.move.batch.importer"
    _inherit = "odoo.delayed.batch.importer"
    _apply_on = ["odoo.stock.move"]

    def run(self, filters=None, force=False):
        """Run the synchronization"""

        updated_ids = self.backend_adapter.search(filters)
        _logger.info(
            "search for odoo stock move %s returned %s items",
            filters,
            len(updated_ids),
        )
        for move in updated_ids:
            move_id = self.backend_adapter.read(move)
            job_options = {
                "priority": 10,
            }
            self._import_record(move_id.id, job_options=job_options)


class StockMoveImporter(Component):
    _name = "odoo.stock.move.importer"
    _inherit = "odoo.importer"
    _apply_on = ["odoo.stock.move"]

    def _import_dependencies(self, force):
        """Import the dependencies for the record"""
        self._import_dependency(
            self.odoo_record.product_id.id, "odoo.product.product", force=force
        )

        self._import_dependency(
            self.odoo_record.location_id.id, "odoo.stock.location", force=force
        )

        self._import_dependency(
            self.odoo_record.location_dest_id.id, "odoo.stock.location", force=force
        )

        self._import_dependency(
            self.odoo_record.product_uom.id, "odoo.uom.uom", force=force
        )

    def _after_import(self, binding, force=False):
        res = super()._after_import(binding, force)
        if binding.picking_id.queue_job_ids:
            pending = binding.picking_id.queue_job_ids.filtered(
                lambda x: x.state != "done" and x.args[1] != self.odoo_record.id
            )
            if not pending and binding.picking_id.bind_ids:
                if (
                    binding.picking_id.purchase_id
                    and binding.picking_id.purchase_id.bind_ids
                    and binding.picking_id.purchase_id.bind_ids[0].backend_state
                    == "done"
                ):
                    binding.picking_id.purchase_id.button_confirm()
        return res


class StockMoveImportMapper(Component):
    _name = "odoo.stock.move.import.mapper"
    _inherit = "odoo.import.mapper"
    _apply_on = "odoo.stock.move"

    direct = [
        ("product_qty", "product_uom_qty"),
        ("date", "date"),
        ("date_expected", "date_deadline"),
        ("name", "name"),
    ]

    @mapping
    def picking_id(self, record):
        binder = self.binder_for("odoo.stock.picking")
        return {"picking_id": binder.to_internal(record.picking_id.id, unwrap=True).id}

    @mapping
    def product_id(self, record):
        binder = self.binder_for("odoo.product.product")
        return {"product_id": binder.to_internal(record.product_id.id, unwrap=True).id}

    @mapping
    def location_id(self, record):
        binder = self.binder_for("odoo.stock.location")
        return {
            "location_id": binder.to_internal(record.location_id.id, unwrap=True).id
        }

    @mapping
    def location_dest_id(self, record):
        binder = self.binder_for("odoo.stock.location")
        return {
            "location_dest_id": binder.to_internal(
                record.location_dest_id.id, unwrap=True
            ).id
        }

    @mapping
    def product_uom(self, record):
        binder = self.binder_for("odoo.uom.uom")
        return {
            "product_uom": binder.to_internal(record.product_uom.id, unwrap=True).id
        }

    @mapping
    def purchase_line_id(self, record):
        binder = self.binder_for("odoo.purchase.order.line")
        return {
            "purchase_line_id": binder.to_internal(
                record.purchase_line_id.id, unwrap=True
            ).id
        }
