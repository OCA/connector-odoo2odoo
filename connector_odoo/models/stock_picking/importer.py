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
        have_lines = len(self.odoo_record["move_lines"]) > 0
        if not have_lines:
            return True
        binding = self._get_binding()
        if binding and binding.state in ["done", "cancel"]:
            return True
        return False

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
            else:
                binding.with_delay()._set_state()
        return res

    def _get_binding_odoo_id_changed(self, binding):
        if binding:
            return binding
        record = self.odoo_record
        if record.sale_id and record.move_lines:
            # If picking is created when changing state importing of sale order
            binder = self.binder_for("odoo.sale.order")
            sale_id = binder.to_internal(record.sale_id.id, unwrap=True)
            move_id = False
            for move in record.move_lines:
                move_id = move
                break
            mapper = self.component(usage="import.mapper")
            picking_type_id = mapper.get_picking_type_from_external_locations(
                "picking", record, move_id.location_id, move_id.location_dest_id
            )
            existing_picking_id = sale_id.picking_ids.filtered(
                lambda x: x.picking_type_id == picking_type_id
            )
            if existing_picking_id:
                return self.env["odoo.stock.picking"].create(
                    {
                        "odoo_id": existing_picking_id.id,
                        "backend_id": self.backend_record.id,
                        "external_id": record.id,
                    }
                )
        return binding


class OdooPickingMapper(Component):
    _name = "odoo.stock.picking.mapper"
    _inherit = "odoo.import.mapper"
    _apply_on = "odoo.stock.picking"

    direct = [("name", "name"), ("origin", "origin"), ("state", "backend_state")]

    @mapping
    def odoo_id(self, record):
        if record.sale_id and record.move_lines:
            binder = self.binder_for("odoo.stock.picking")
            picking_id = binder.to_internal(record.id, unwrap=True)
            if picking_id:
                return {"odoo_id": picking_id.id}
            else:
                # If picking is created when changing state importing sale order
                binder = self.binder_for("odoo.sale.order")
                sale_id = binder.to_internal(record.sale_id.id, unwrap=True)
                move_id = False
                for move in record.move_lines:
                    move_id = move
                    break
                picking_type_id = self.get_picking_type_from_external_locations(
                    "picking", record, move_id.location_id, move_id.location_dest_id
                )
                existing_picking_id = sale_id.picking_ids.filtered(
                    lambda x: x.picking_type_id == picking_type_id
                )
                if existing_picking_id:
                    return {"odoo_id": existing_picking_id.id}
        return {}

    def get_picking_type_from_external_locations(
        self, model_label, record, location_id, location_dest_id
    ):
        binder = self.binder_for("odoo.stock.location")
        location_id = binder.to_internal(location_id.id, unwrap=True)
        warehouse_id = location_id.warehouse_id
        if not warehouse_id:
            location_id = binder.to_internal(location_dest_id.id, unwrap=True)
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
                    "and type {} from {} {}-{}. "
                    "Please go to configuration connector picking type mapping "
                    "and include warehouse and type char field value"
                ).format(
                    warehouse_id.id,
                    warehouse_id.name,
                    record["type"],
                    model_label,
                    record["id"],
                    record["name"],
                )
            )
        if len(picking_type_mapping_id) != 1:
            picking_type_mapping_id = picking_type_mapping_id.filtered(
                lambda x: x.origin_location_usage == location_id.usage
            )
            if len(picking_type_mapping_id) != 1:
                picking_type_mapping_id = picking_type_mapping_id.filtered(
                    lambda x: x.dest_location_usage == location_dest_id.usage
                )
        return picking_type_mapping_id.picking_type_id

    @mapping
    def picking_type_id(self, record):
        picking_binder = self.binder_for("odoo.stock.picking").to_internal(record["id"])
        if picking_binder:
            return {}
        if len(record["move_lines"]) <= 0:
            return {}
        for move in record["move_lines"]:
            move_id = move
            break
        picking_type_id = self.get_picking_type_from_external_locations(
            "picking", record, move_id.location_id, move_id.location_dest_id
        )
        return {"picking_type_id": picking_type_id.id}

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
        if record["partner_id"]:
            binder = self.binder_for("odoo.res.partner")
            partner_id = binder.to_internal(record["partner_id"].id, unwrap=True)
            return {"partner_id": partner_id.id if partner_id else False}
