# Copyright 2013-2017 Camptocamp SA
# © 2016 Sodexis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import fields, models

from odoo.addons.component.core import Component
from odoo.addons.component_event.components.event import skip_if

_logger = logging.getLogger(__name__)


class OdooSaleOrder(models.Model):
    _name = "odoo.sale.order"
    _inherit = "odoo.binding"
    _inherits = {"sale.order": "odoo_id"}
    _description = "External Odoo Sale Order"

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
            return self.with_delay().import_record(self.backend_id, self.external_id)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    bind_ids = fields.One2many(
        comodel_name="odoo.sale.order",
        inverse_name="odoo_id",
        string="Odoo Bindings",
    )

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        self._event("on_sale_order_confirm").notify(self)
        return res


class SaleOrderAdapter(Component):
    _name = "odoo.sale.order.adapter"
    _inherit = "odoo.adapter"
    _apply_on = "odoo.sale.order"
    _odoo_model = "sale.order"


class SaleOrderListener(Component):
    _name = "odoo.sale.order.listener"
    _inherit = "base.connector.listener"
    _apply_on = ["sale.order"]
    _usage = "event.listener"

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_sale_order_confirm(self, record):
        # FIXME: do the proper way
        bind_model = self.env["odoo.sale.order"]
        backend = self.env["odoo.backend"].search([])
        if backend:
            binding = bind_model.create(
                {
                    "backend_id": backend[0].id,
                    "odoo_id": record.id,
                    "external_id": 0,
                }
            )
            binding.with_delay().export_record(backend)
        else:
            _logger.info("No backend found for sale order %s", record.id)


class OdooSaleOrderLine(models.Model):
    _name = "odoo.sale.order.line"
    _inherit = "odoo.binding"
    _inherits = {"sale.order.line": "odoo_id"}
    _description = "External Odoo Sale Order Line"

    def resync(self):
        if self.backend_id.product_main_record == "odoo":
            return self.with_delay().export_record(self.backend_id)
        else:
            return self.with_delay().import_record(self.backend_id, self.external_id)


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    bind_ids = fields.One2many(
        comodel_name="odoo.sale.order.line",
        inverse_name="odoo_id",
        string="Odoo Bindings",
    )
