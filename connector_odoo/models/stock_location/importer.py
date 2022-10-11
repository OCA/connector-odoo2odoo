# Copyright 2022 Greenice, S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import logging

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping

_logger = logging.getLogger(__name__)


class StockLocationBatchImporter(Component):
    _name = "odoo.stock.location.batch.importer"
    _inherit = "odoo.delayed.batch.importer"
    _apply_on = ["odoo.stock.location"]

    def run(self, filters=None, force=False):
        """Run the synchronization"""
        external_ids = self.backend_adapter.search(
            filters,
        )
        _logger.info(
            "search for odoo Location %s returned %s items",
            filters,
            len(external_ids),
        )
        for external_id in external_ids:
            job_options = {
                "priority": 15,
            }
            self._import_record(external_id, job_options=job_options)


class StockLocationImporter(Component):
    _name = "odoo.stock.location.importer"
    _inherit = "odoo.importer"
    _apply_on = ["odoo.stock.location"]

    def _import_dependencies(self, force=False):
        """Import the dependencies for the record"""
        # import parent
        _logger.info("Importing dependencies for external ID %s", self.external_id)
        if self.odoo_record.location_id:
            _logger.info("Importing location parent")
            self._import_dependency(
                self.odoo_record.location_id.id, "odoo.stock.location", force=force
            )

        result = super()._import_dependencies(force=force)
        _logger.info("Dependencies imported for external ID %s", self.external_id)
        return result


class StockLocationImportMapper(Component):
    _name = "odoo.stock.location.import.mapper"
    _inherit = "odoo.import.mapper"
    _apply_on = "odoo.stock.location"

    direct = [
        ("name", "name"),
        ("usage", "usage"),
    ]

    @mapping
    def usage(self, record):
        usage = record.usage
        if usage == "external":
            usage = "internal"
        return {"usage": usage}

    @mapping
    def odoo_id(self, record):
        odoo_id = False
        binder = self.binder_for("odoo.stock.location")
        location_id = binder.to_internal(record.id, unwrap=True)
        parent_location_id = False
        if location_id:
            odoo_id = location_id.id
        else:
            if record.location_id:
                parent_location_id = binder.to_internal(
                    record.location_id.id, unwrap=True
                )
            warehouse_id = (
                location_id.warehouse_id.id if location_id.warehouse_id else False
            )
            location_id = self.env["stock.location"].search(
                [
                    ("name", "=", record.name),
                    ("warehouse_id", "=", warehouse_id),
                    (
                        "location_id",
                        "=",
                        parent_location_id.id if parent_location_id else False,
                    ),
                ]
            )
            if location_id:
                odoo_id = location_id[0].id
        return {"odoo_id": odoo_id}

    @mapping
    def location_id(self, record):
        location_id = False
        if record.location_id:
            binder = self.binder_for("odoo.stock.location")
            location_id = binder.to_internal(record.location_id.id, unwrap=True)
            location_id = location_id.id
        return {"location_id": location_id}
