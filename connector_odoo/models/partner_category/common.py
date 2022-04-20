# Copyright 2013-2017 Camptocamp SA
# © 2016 Sodexis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import fields, models

from odoo.addons.component.core import Component
from odoo.addons.component_event.components.event import skip_if

_logger = logging.getLogger(__name__)


class OdooPartnerCategory(models.Model):
    _name = "odoo.res.partner.category"
    _inherit = "odoo.binding"
    _inherits = {"res.partner.category": "odoo_id"}
    _description = "External Odoo Partner Category"

    def resync(self):
        if self.backend_id.partner_main_record == "odoo":
            return self.with_delay().export_record(self.backend_id)
        else:
            return self.with_delay().import_record(
                self.backend_id, self.external_id, force=True
            )


class PartnerCategory(models.Model):
    _inherit = "res.partner.category"

    bind_ids = fields.One2many(
        comodel_name="odoo.res.partner.category",
        inverse_name="odoo_id",
        string="Odoo Bindings",
    )


class PartnerCategoryAdapter(Component):
    _name = "odoo.res.partner.category.adapter"
    _inherit = "odoo.adapter"
    _apply_on = "odoo.res.partner.category"

    _odoo_model = "res.partner.category"


class PartnerCategoryListener(Component):
    _name = "res.partner.category.listener"
    _inherit = "base.connector.listener"
    _apply_on = ["res.partner.category"]
    _usage = "event.listener"

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_create(self, record, fields=None):
        # FIXME: do the proper way
        bind_model = self.env["odoo.res.partner.category"]
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
            _logger.info("No backend found for partner %s", record.id)
