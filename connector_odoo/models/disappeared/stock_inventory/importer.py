# Copyright 2022 Greenice, S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)
import logging

from odoo.addons.component.core import Component

_logger = logging.getLogger(__name__)


class StockInventoryDisappearedBatchImporter(Component):
    """Import the Odoo Picking from Stock Inventory (OpenERP Model deprecated).

    For every Stock inventory in the list, a delayed job is created.
    Import from a date
    """

    _name = "odoo.stock.inventory.disappeared.batch.importer"
    _inherit = "odoo.delayed.batch.importer"
    _apply_on = ["odoo.stock.inventory.disappeared"]

    def run(self, filters=None, force=False):
        """Run the synchronization"""
        inventory_model = self.backend_record.get_connection().api.get(
            "stock.inventory"
        )
        external_ids = inventory_model.search(filters)

        _logger.info(
            "search for odoo stock inventory %s returned %s items",
            filters,
            len(external_ids),
        )
        for external_id in external_ids:
            job_options = {"priority": 15}
            self._import_record(external_id, job_options=job_options, force=force)


class StockInventoryDisappearedImporter(Component):
    _name = "odoo.stock.inventory.disappeared.importer"
    _inherit = "odoo.importer"
    _apply_on = ["odoo.stock.inventory.disappeared"]

    def _init_import(self, binding, external_id):
        self.import_stock_inventory(self.backend_record, external_id)
        super()._init_import(binding, external_id)
        return False

    def import_stock_inventory(self, backend_record, inventory_id):
        _logger.info("Obtaining stock inventory {}".format(inventory_id))
        inventory_model = backend_record.get_connection().api.get("stock.inventory")

        inventory = inventory_model.browse(inventory_id)
        if len(inventory["move_ids"]) <= 0:
            return {}
        for move in inventory["move_ids"]:
            move_id = move
            break
        self._import_dependency(move_id.location_id.id, "odoo.stock.location")
        self._import_dependency(move_id.location_dest_id.id, "odoo.stock.location")
        payload = self.default_stock_inventory_values(
            inventory, move_id.location_id, move_id.location_dest_id
        )
        binder = self.binder_for("odoo.stock.inventory.disappeared")
        binding = binder.to_internal(inventory_id, unwrap=False)

        if binding:
            binding.write(payload)
        else:
            payload = {
                **payload,
                **{
                    "backend_id": backend_record.id,
                    "external_id": inventory_id,
                },
            }
            binding = binding.with_context(connector_no_export=True).create(payload)
        self.after_import_stock_inventory(backend_record, binding, inventory)

    def default_stock_inventory_values(self, inventory, location_id, location_dest_id):
        picking_importer = self.component(
            usage="import.mapper", model_name="odoo.stock.picking"
        )
        binder = self.binder_for("odoo.stock.location")
        record = {
            "id": inventory["id"],
            "name": inventory["name"],
            "type": "internal",
        }
        picking_type_id = picking_importer.get_picking_type_from_external_locations(
            "inventory", record, location_id, location_dest_id
        )
        location_id = binder.to_internal(location_id.id, unwrap=True)
        location_dest_id = binder.to_internal(location_dest_id.id, unwrap=True)
        return {
            "picking_type_id": picking_type_id.id,
            "location_id": location_id.id,
            "location_dest_id": location_dest_id.id,
            "origin": inventory["name"],
            "backend_state": inventory["state"],
        }

    def after_import_stock_inventory(self, backend_record, binding, inventory):
        _logger.info("After import stock inventory {}".format(binding.external_id))
        if inventory.move_ids:
            delayed_line_ids = []
            for line_id in inventory.move_ids:
                stock_move_model = self.env["odoo.stock.move"]
                if backend_record.delayed_import_lines:
                    stock_move_model = stock_move_model.with_delay()
                delayed_line_id = stock_move_model.import_record(
                    backend_record,
                    line_id.id,
                    force=True,
                    picking_id=binding.odoo_id.id,
                )
                if backend_record.delayed_import_lines:
                    delayed_line_id = self.env["queue.job"].search(
                        [("uuid", "=", delayed_line_id.uuid)]
                    )
                    delayed_line_ids.append(delayed_line_id.id)
            if backend_record.delayed_import_lines:
                binding.queue_job_ids = [
                    (6, 0, (delayed_line_ids + binding.queue_job_ids.ids))
                ]
            else:
                self.with_delay()._set_inventory_state()
