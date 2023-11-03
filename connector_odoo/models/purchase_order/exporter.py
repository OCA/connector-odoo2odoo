# Copyright 2022 GreenIce, S.L. <https://greenice.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import ExportMapChild, mapping

# from odoo.addons.connector.exception import MappingError

_logger = logging.getLogger(__name__)


class OdooPurchaseOrderExporter(Component):
    _name = "odoo.purchase.order.exporter"
    _inherit = "odoo.exporter"
    _apply_on = ["odoo.purchase.order"]

    def _get_partner(self, record_partner):
        partner_ids = record_partner.bind_ids
        partner = self.env["odoo.res.partner"]
        if partner_ids:
            partner = partner_ids.filtered(
                lambda c: c.backend_id == self.backend_record
            )
        if not partner:
            partner = self.env["odoo.res.partner"].create(
                {
                    "odoo_id": record_partner.id,
                    "external_id": 0,
                    "backend_id": self.backend_record.id,
                }
            )
        return partner

    def _export_dependencies(self):
        # FIXME: This doesn't seem right
        if not self.binding.partner_id:
            return
        for record_partner in [self.binding.partner_id]:
            partner = self._get_partner(record_partner)
            bind_partner = self.binder.to_external(partner, wrap=False)
            if not bind_partner:
                self._export_dependency(partner, "odoo.res.partner")


class PurchaseOrderExportMapper(Component):
    _name = "odoo.purchase.order.export.mapper"
    _inherit = "odoo.export.mapper"
    _apply_on = ["odoo.purchase.order"]

    direct = [
        ("partner_ref", "partner_ref"),
        ("origin", "origin"),
        ("date_order", "date_order"),
    ]

    children = [("order_line", "order_line", "odoo.purchase.order.line")]

    @mapping
    def partner_id(self, record):
        binder = self.binder_for("odoo.res.partner")
        return {"partner_id": binder.to_external(record.partner_id, wrap=True)}


class PurchaseOrderLineExportMapper(Component):
    _name = "odoo.purchase.order.line.export.mapper"
    _inherit = "odoo.export.mapper"
    _apply_on = ["odoo.purchase.order.line"]

    direct = [
        ("name", "name"),
        ("price_unit", "price_unit"),
        ("product_uom_qty", "product_uom_qty"),
        ("date_planned", "date_planned"),
    ]

    @mapping
    def product_id(self, record):
        binder = self.binder_for("odoo.product.product")
        return {
            "product_id": binder.to_external(record.product_id, wrap=True),
        }


class PurchaseOrderExportMapChild(ExportMapChild):
    _model_name = "odoo.purchase.order"

    def format_items(self, items_values):
        return [(0, 0, item) for item in items_values]
