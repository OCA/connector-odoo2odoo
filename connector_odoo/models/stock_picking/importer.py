# Copyright 2022 Greenice, S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import logging

from odoo import _
from odoo.exceptions import ValidationError

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping

_logger = logging.getLogger(__name__)


class StockPickingBatchImporter(Component):
    _name = "odoo.stock.picking.batch.importer"
    _inherit = "odoo.delayed.batch.importer"
    _apply_on = ["odoo.stock.picking"]

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


class StockPickingImporter(Component):
    _name = "odoo.stock.picking.importer"
    _inherit = "odoo.importer"
    _apply_on = ["odoo.stock.picking"]

    def _must_skip(
        self,
    ):
        if self.backend_record.version != "6.1":
            raise ValidationError(_("Only OpenERP 6.1 is supported"))
        return len(self.odoo_record["move_lines"]) <= 0

    def _import_dependencies(self, force=False):
        """Import the dependencies for the record"""
        for move_id in self.odoo_record["move_lines"]:
            self._import_dependency(
                move_id.location_id.id, "odoo.stock.location", force=force
            )

            self._import_dependency(
                move_id.location_dest_id.id, "odoo.stock.location", force=force
            )
            break
        if self.odoo_record["partner_id"]:
            self._import_dependency(
                self.odoo_record["partner_id"].id, "odoo.res.partner", force=force
            )

    def _after_import(self, binding, force=False):
        res = super()._after_import(binding, force)
        if self.odoo_record.move_lines:
            delayed_line_ids = []
            for line_id in self.odoo_record.move_lines:
                stock_move_model = self.env["odoo.stock.move"]
                if self.backend_record.delayed_import_lines:
                    stock_move_model = stock_move_model.with_delay()
                delayed_line_id = stock_move_model.import_record(
                    self.backend_record, line_id.id, force=True
                )
                if self.backend_record.delayed_import_lines:
                    delayed_line_id = self.env["queue.job"].search(
                        [("uuid", "=", delayed_line_id.uuid)]
                    )
                    delayed_line_ids.append(delayed_line_id.id)
            if self.backend_record.delayed_import_lines:
                binding.queue_job_ids = [
                    (6, 0, (delayed_line_ids + binding.queue_job_ids.ids))
                ]
        return res


class OdooPickingMapper(Component):
    _name = "odoo.stock.picking.mapper"
    _inherit = "odoo.import.mapper"
    _apply_on = "odoo.stock.picking"

    direct = [
        ("name", "name"),
        ("origin", "origin"),
    ]

    @mapping
    def picking_type_id(self, record):
        if len(record["move_lines"]) <= 0:
            return {}
        for move in record["move_lines"]:
            move_id = move
            break
        binder = self.binder_for("odoo.stock.location")
        location_id = binder.to_internal(move_id.location_id.id, unwrap=True)
        warehouse_id = location_id.warehouse_id
        if not warehouse_id:
            location_id = binder.to_internal(move_id.location_dest_id.id, unwrap=True)
            warehouse_id = location_id.warehouse_id

        picking_type_mapping_id = self.env["openerp.picking.type"].search(
            [
                ("warehouse_id.odoo_id.id", "=", warehouse_id.id),
                ("type", "=", record["type"]),
            ]
        )
        if not picking_type_mapping_id:
            raise ValidationError(
                _(
                    "No picking type found for warehouse {}-{} "
                    "and type {} from picking {}-{}. "
                    "Please go to configuration connector picking type mapping "
                    "and include warehouse and type char field value"
                ).format(
                    warehouse_id.id,
                    warehouse_id.name,
                    record.type,
                    record["id"],
                    record["name"],
                )
            )
        if len(picking_type_mapping_id) != 1:
            picking_type_mapping_id = picking_type_mapping_id.filtered(
                lambda x: x.origin_location_usage == move_id.location_id.usage
            )
            if len(picking_type_mapping_id) != 1:
                picking_type_mapping_id = picking_type_mapping_id.filtered(
                    lambda x: x.dest_location_usage == move_id.location_dest_id.usage
                )
        return {"picking_type_id": picking_type_mapping_id.picking_type_id.id}

    @mapping
    def location_id(self, record):
        binder = self.binder_for("odoo.stock.location")
        location_id = False
        move_id = list(record["move_lines"])[0]
        location_id = binder.to_internal(move_id.location_id.id, unwrap=True)
        return {"location_id": location_id.id}

    @mapping
    def location_dest_id(self, record):
        binder = self.binder_for("odoo.stock.location")
        move_id = list(record["move_lines"])[0]
        location_dest_id = binder.to_internal(move_id.location_dest_id.id, unwrap=True)
        return {"location_dest_id": location_dest_id.id}

    @mapping
    def partner_id(self, record):
        binder = self.binder_for("odoo.res.partner")
        partner_id = binder.to_internal(record["partner_id"].id, unwrap=True)
        return {"partner_id": partner_id.id if partner_id else False}
