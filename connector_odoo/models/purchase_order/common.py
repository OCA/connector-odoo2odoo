# Copyright 2022 GreenIce, S.L. <https://greenice.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import fields, models

from odoo.addons.component.core import Component
from odoo.addons.component_event.components.event import skip_if

_logger = logging.getLogger(__name__)


class OdooPurchaseOrder(models.Model):
    _name = "odoo.purchase.order"
    _inherit = "odoo.binding"
    _inherits = {"purchase.order": "odoo_id"}
    _description = "External Odoo Purchase Order"

    backend_amount_total = fields.Float()
    backend_amount_tax = fields.Float()

    _sql_constraints = [
        (
            "external_id",
            "UNIQUE(external_id)",
            "External ID (external_id) must be unique!",
        ),
    ]

    def name_get(self):
        result = []
        for op in self:
            name = "{} (Backend: {})".format(
                op.odoo_id.display_name, op.backend_id.display_name
            )
            result.append((op.id, name))

        return result

    def resync(self):
        if self.backend_id.product_main_record == "odoo":
            return self.with_delay().export_record(self.backend_id)
        else:
            return self.with_delay().import_record(
                self.backend_id, self.external_id, force=True
            )


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    bind_ids = fields.One2many(
        comodel_name="odoo.purchase.order",
        inverse_name="odoo_id",
        string="Odoo Bindings",
    )

    def button_confirm(self):
        res = super(PurchaseOrder, self).button_confirm()
        self._event("on_purchase_order_confirm").notify(self)
        return res


class PurchaseOrderAdapter(Component):
    _name = "odoo.purchase.order.adapter"
    _inherit = "odoo.adapter"
    _apply_on = "odoo.purchase.order"
    _odoo_model = "purchase.order"


class PurchaseOrderListener(Component):
    _name = "odoo.purchase.order.listener"
    _inherit = "base.connector.listener"
    _apply_on = ["purchase.order"]
    _usage = "event.listener"

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_sale_order_confirm(self, record):
        _logger.info("Not implemented yet. Ignoring on_sale_order_confirm  %s", record)


class OdooPurchaseOrderLine(models.Model):
    _name = "odoo.purchase.order.line"
    _inherit = "odoo.binding"
    _inherits = {"purchase.order.line": "odoo_id"}
    _description = "External Odoo Purchase Order Line"

    def resync(self):
        if self.backend_id.product_main_record == "odoo":
            return self.with_delay().export_record(self.backend_id)
        else:
            return self.with_delay().import_record(
                self.backend_id, self.external_id, force=True
            )


class PurchaseOrderLineAdapter(Component):
    _name = "odoo.purchase.order.line.adapter"
    _inherit = "odoo.adapter"
    _apply_on = "odoo.purchase.order.line"
    _odoo_model = "purchase.order.line"


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    bind_ids = fields.One2many(
        comodel_name="odoo.purchase.order.line",
        inverse_name="odoo_id",
        string="Odoo Bindings",
    )
