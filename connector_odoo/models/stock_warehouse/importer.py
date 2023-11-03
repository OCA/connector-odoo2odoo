# Copyright 2022 Greenice, S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import logging

from odoo import _
from odoo.exceptions import ValidationError

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping, only_create

_logger = logging.getLogger(__name__)


class StockWarehouseBatchImporter(Component):
    _name = "odoo.stock.warehouse.batch.importer"
    _inherit = "odoo.delayed.batch.importer"
    _apply_on = ["odoo.stock.warehouse"]

    def run(self, filters=None, force=False):
        """Run the synchronization"""
        external_ids = self.backend_adapter.search(
            filters,
        )
        _logger.info(
            "search for odoo Warehouse %s returned %s items",
            filters,
            len(external_ids),
        )
        for external_id in external_ids:
            job_options = {
                "priority": 15,
            }
            self._import_record(external_id, job_options=job_options)


class StockWarehouseImporter(Component):
    _name = "odoo.stock.warehouse.importer"
    _inherit = "odoo.importer"
    _apply_on = ["odoo.stock.warehouse"]

    def _import_dependencies(self, force=False):
        """Import the dependencies for the record"""
        record = self.odoo_record
        if self.backend_record.version == "6.1":
            input_location_id = record.lot_input_id.id
        else:
            input_location_id = record.wh_input_stock_loc_id.id
        self._import_dependency(input_location_id, "odoo.stock.location", force=force)

        if self.backend_record.version == "6.1":
            output_location_id = record.lot_output_id.id
        else:
            output_location_id = record.wh_output_stock_loc_id.id
        self._import_dependency(output_location_id, "odoo.stock.location", force=force)

        if self.backend_record.version == "6.1":
            pack_location_id = (
                record.lot_reception_id.id if record.lot_reception_id else False
            )
        else:
            pack_location_id = (
                record.wh_pack_stock_loc_id.id if record.wh_pack_stock_loc_id else False
            )
        if pack_location_id:
            self._import_dependency(
                pack_location_id, "odoo.stock.location", force=force
            )
        lot_stock_id = record.lot_stock_id.id
        self._import_dependency(lot_stock_id, "odoo.stock.location", force=force)


class WarehouseMapper(Component):
    _name = "odoo.stock.warehouse.mapper"
    _inherit = "odoo.import.mapper"
    _apply_on = "odoo.stock.warehouse"

    @mapping
    def code(self, record):
        if self.backend_record.version == "6.1":
            code = (
                record.launching_sequence_id.prefix
                if record.launching_sequence_id
                else record.name.replace(" ", "_")
            )
        else:
            code = record.code
        return {"code": code}

    @only_create
    @mapping
    def check_warehouse_exists(self, record):
        res = {}
        if self.backend_record.version == "6.1":
            code = (
                record.launching_sequence_id.prefix
                if record.launching_sequence_id
                else record.name.replace(" ", "_")
            )
        else:
            code = record.code
        warehouse_id = self.env["stock.warehouse"].search([("code", "=", code)])
        _logger.debug("Warehouse found for %s : %s" % (record, warehouse_id))
        if len(warehouse_id) == 1:
            res.update({"odoo_id": warehouse_id.id})
        else:
            raise ValidationError(
                _(
                    "Warehouse code %s not found. "
                    "Only can link existing warehouse. Create it manually"
                )
                % code
            )
        return res

    @mapping
    def wh_input_stock_loc_id(self, record):
        binder = self.binder_for("odoo.stock.location")
        if self.backend_record.version == "6.1":
            location_id = binder.to_internal(record.lot_input_id.id)
        else:
            location_id = binder.to_internal(record.wh_input_stock_loc_id.id)
        if location_id:
            return {"wh_input_stock_loc_id": location_id.odoo_id.id}
        else:
            return {}

    @mapping
    def wh_output_stock_loc_id(self, record):
        binder = self.binder_for("odoo.stock.location")
        if self.backend_record.version == "6.1":
            location_id = binder.to_internal(record.lot_output_id.id)
        else:
            location_id = binder.to_internal(record.wh_output_stock_loc_id.id)
        if location_id:
            return {"wh_output_stock_loc_id": location_id.odoo_id.id}
        else:
            return {}

    @mapping
    def wh_pack_stock_loc_id(self, record):
        binder = self.binder_for("odoo.stock.location")
        location_id = False
        if self.backend_record.version == "6.1":
            if record.lot_reception_id:
                location_id = binder.to_internal(record.lot_reception_id.id)
        else:
            if record.wh_pack_stock_loc_id:
                location_id = binder.to_internal(record.wh_pack_stock_loc_id.id)
        return {
            "wh_pack_stock_loc_id": location_id.odoo_id.id if location_id else False
        }

    @mapping
    def lot_stock_id(self, record):
        binder = self.binder_for("odoo.stock.location")
        location_id = binder.to_internal(record.lot_stock_id.id)
        if location_id:
            parent_location_id = binder.to_internal(record.lot_stock_id.location_id.id)
            return {
                "lot_stock_id": location_id.odoo_id.id,
                "view_location_id": parent_location_id.odoo_id.id,
            }
        else:
            return {}
