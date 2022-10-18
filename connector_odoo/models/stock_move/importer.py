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

    def _must_skip(self):
        binding = self._get_binding()
        if binding and binding.state in ["done", "cancel"]:
            return True
        return super()._must_skip()

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
        if self.backend_record.delayed_import_lines:
            pending = binding.picking_id.queue_job_ids.filtered(
                lambda x: x.state != "done" and x.args[1] != self.odoo_record.id
            )
            ok_purchase = (
                binding.picking_id.purchase_id
                and binding.picking_id.purchase_id.bind_ids
                and binding.picking_id.purchase_id.bind_ids[0].backend_picking_count
                == len(binding.picking_id.purchase_id.picking_ids)
            )
            ok_sale = (
                binding.sale_line_id
                and binding.sale_line_id.order_id.bind_ids
                and binding.sale_line_id.order_id.bind_ids.backend_picking_count
                == len(binding.sale_line_id.order_id.picking_ids)
            )

            # The last stock move of the last picking of purchase/sale
            if not pending and ok_purchase:
                binder = self.binder_for("odoo.purchase.order")
                purchase_binding = binder.to_internal(binding.picking_id.purchase_id.id)
                purchase_binding.with_delay()._set_state()
            elif not pending and ok_sale:
                sale_binding = binding.sale_line_id.order_id.bind_ids[0]
                sale_binding.with_delay()._set_state()
            # The last stock move of the last picking of picking
            elif not pending:
                binder = self.binder_for("odoo.stock.picking")
                picking_binding = binder.to_internal(binding.picking_id.id)
                if picking_binding:
                    picking_binding.with_delay()._set_state()
                else:
                    inventory_binding = self.env[
                        "odoo.stock.inventory.disappeared"
                    ].search([("odoo_id", "=", binding.picking_id.id)])
                    if inventory_binding:
                        inventory_binding.with_delay()._set_inventory_state()

        return res

    def _get_binding_odoo_id_changed(self, binding):
        if binding:
            return binding
        if self.odoo_record.picking_id.sale_id:
            # If move is created when changing state importing of sale order
            binder = self.binder_for("odoo.sale.order")
            sale_id = binder.to_internal(
                self.odoo_record.picking_id.sale_id.id, unwrap=True
            )
            mapper = self.component(
                usage="import.mapper", model_name="odoo.stock.picking"
            )
            picking_type_id = mapper.get_picking_type_from_external_locations(
                "move",
                self.odoo_record.picking_id,
                self.odoo_record.location_id,
                self.odoo_record.location_dest_id,
            )
            existing_picking_id = sale_id.picking_ids.filtered(
                lambda x: x.picking_type_id == picking_type_id
            )
            product_binder = self.binder_for("odoo.product.product")
            product_id = product_binder.to_internal(
                self.odoo_record.product_id.id, unwrap=True
            )
            existing_move_id = (
                existing_picking_id.move_lines.filtered(
                    lambda x: x.product_id == product_id and not x.bind_ids
                )
                if existing_picking_id
                else False
            )
            if existing_move_id:
                return self.env["odoo.stock.move"].create(
                    {
                        "odoo_id": existing_move_id[0].id,
                        "backend_id": self.backend_record.id,
                        "external_id": self.odoo_record.id,
                    }
                )
        return binding


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
        if not record.picking_id:
            picking = self.backend_record._context.get("picking_id")
        else:
            picking = binder.to_internal(record.picking_id.id, unwrap=True).id

        return {"picking_id": picking}

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
        if record.purchase_line_id:
            binder = self.binder_for("odoo.purchase.order.line")
            return {
                "purchase_line_id": binder.to_internal(
                    record.purchase_line_id.id, unwrap=True
                ).id
            }

    @mapping
    def sale_line_id(self, record):
        if record.sale_line_id:
            binder = self.binder_for("odoo.sale.order.line")
            return {
                "sale_line_id": binder.to_internal(
                    record.sale_line_id.id, unwrap=True
                ).id
            }
